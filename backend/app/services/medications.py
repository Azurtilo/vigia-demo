"""Medicamentos y registro de tomas.

- Las tomas programadas NO se guardan por adelantado: se calculan desde el horario (app.core.schedule).
- Un registro de toma programada tiene ID determinista {medId}_{instanteUTC}: no puede registrarse
  dos veces, ni con solicitudes simultáneas.
- Cada cambio de un medicamento guarda la versión anterior completa en `revisions`.
"""

from datetime import UTC, date, datetime

from fastapi import status
from google.api_core.exceptions import Aborted, AlreadyExists
from google.cloud import firestore

from app.core.errors import AppError
from app.core.firebase import get_db
from app.core.schedule import local_date_of, occurrence_key, occurrences_on
from app.models.medication import (
    DoseLog,
    DoseLogCorrection,
    DoseLogCreate,
    Medication,
    MedicationCreate,
    MedicationUpdate,
)
from app.services import patients as patients_service
from app.services.activity import activity_entry, activity_ref
from app.services.audit import audit_entry, audit_ref
from app.services.care_common import (
    CLOCK_SKEW,
    patient_tz,
    require_active_patient,
    schedule_from,
    schedule_to,
    unprocessable,
)


def meds_collection(patient_id: str) -> firestore.CollectionReference:
    return get_db().collection("patients").document(patient_id).collection("medications")


def logs_collection(patient_id: str) -> firestore.CollectionReference:
    return get_db().collection("patients").document(patient_id).collection("medicationLogs")


# ---------- Conversión Firestore <-> modelos ----------


def to_medication(med_id: str, patient_id: str, d: dict) -> Medication:
    return Medication(
        id=med_id,
        patient_id=patient_id,
        name=d["name"],
        dose=d["dose"],
        instructions=d.get("instructions"),
        schedule_type=d["scheduleType"],
        schedule=schedule_from(d.get("schedule")),
        start_date=date.fromisoformat(d["startDate"]),
        end_date=date.fromisoformat(d["endDate"]) if d.get("endDate") else None,
        active=d["active"],
        created_by=d["createdBy"],
        created_at=d.get("createdAt"),
        updated_at=d.get("updatedAt"),
    )


def _med_fields(body: MedicationCreate | MedicationUpdate, only_sent: bool) -> dict:
    sent = body.model_fields_set if only_sent else set(type(body).model_fields)
    names = {
        "name": "name",
        "dose": "dose",
        "instructions": "instructions",
        "schedule_type": "scheduleType",
        "start_date": "startDate",
        "end_date": "endDate",
        "active": "active",
    }
    out = {}
    for field in sent:
        value = getattr(body, field)
        if field == "schedule":
            out["schedule"] = schedule_to(value)
        elif field in ("start_date", "end_date"):
            out[names[field]] = value.isoformat() if value else None
        else:
            out[names[field]] = value
    return out


def to_log(log_id: str, d: dict) -> DoseLog:
    return DoseLog(
        id=log_id,
        medication_id=d["medicationId"],
        medication_name=d["medicationName"],
        dose=d["dose"],
        scheduled_at=d.get("scheduledAt"),
        status=d["status"],
        actual_at=d.get("actualAt"),
        reason=d.get("reason"),
        recorded_by=d["recordedBy"],
        recorded_at=d.get("recordedAt"),
        corrections=len(d.get("history", [])),
    )


def _validate_merged(d: dict) -> None:
    if d["scheduleType"] == "fixed" and not d.get("schedule"):
        raise unprocessable("schedule_required", "Un medicamento con horario fijo necesita al menos una hora.")
    if d["scheduleType"] == "as_needed" and d.get("schedule"):
        raise unprocessable("schedule_not_allowed", "Un medicamento 'si es necesario' no lleva horario.")
    if d.get("endDate") and d["endDate"] < d["startDate"]:
        raise unprocessable("invalid_dates", "La fecha de término no puede ser anterior a la de inicio.")


# ---------- Medicamentos ----------


def create_medication(patient_id: str, uid: str, body: MedicationCreate) -> Medication:
    access = patients_service.get_access(patient_id, uid, "meds.manage")
    require_active_patient(access)
    db = get_db()
    ref = meds_collection(patient_id).document()
    data = {
        **_med_fields(body, only_sent=False),
        "active": True,
        "createdBy": uid,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    batch = db.batch()
    batch.create(ref, data)
    batch.set(
        activity_ref(patient_id),
        activity_entry("medication.created", uid, datetime.now(UTC), {"medicationId": ref.id, "name": body.name}),
    )
    batch.set(audit_ref(), audit_entry(uid, "medication.created", f"patients/{patient_id}", {"medicationId": ref.id}))
    batch.commit()
    return get_medication(patient_id, uid, ref.id)


def get_medication(patient_id: str, uid: str, med_id: str) -> Medication:
    patients_service.get_access(patient_id, uid, "patient.view")
    snap = meds_collection(patient_id).document(med_id).get()
    if not snap.exists:
        raise AppError(status.HTTP_404_NOT_FOUND, "medication_not_found", "Medicamento no encontrado.")
    return to_medication(snap.id, patient_id, snap.to_dict())


def list_medications(patient_id: str, uid: str, include_inactive: bool) -> list[Medication]:
    patients_service.get_access(patient_id, uid, "patient.view")
    meds = [to_medication(s.id, patient_id, s.to_dict()) for s in meds_collection(patient_id).stream()]
    meds = [m for m in meds if include_inactive or m.active]
    return sorted(meds, key=lambda m: (not m.active, m.name.lower()))


def update_medication(patient_id: str, uid: str, med_id: str, body: MedicationUpdate) -> Medication:
    access = patients_service.get_access(patient_id, uid, "meds.manage")
    require_active_patient(access)
    changes = _med_fields(body, only_sent=True)
    if not changes:
        return get_medication(patient_id, uid, med_id)
    if changes.get("scheduleType") == "as_needed" and "schedule" not in changes:
        changes["schedule"] = None  # pasar a "si es necesario" elimina el horario
    required = {"name", "dose", "scheduleType", "startDate", "active"}
    if any(changes[k] is None for k in required & changes.keys()):
        raise unprocessable("validation_error", "Nombre, dosis, tipo de horario, inicio y estado no pueden quedar vacíos.")
    db = get_db()
    ref = meds_collection(patient_id).document(med_id)

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        snap = ref.get(transaction=transaction)
        if not snap.exists:
            raise AppError(status.HTTP_404_NOT_FOUND, "medication_not_found", "Medicamento no encontrado.")
        current = snap.to_dict()
        _validate_merged({**current, **changes})
        # Versión anterior completa: permite ver qué decía antes y quién lo cambió.
        transaction.set(
            ref.collection("revisions").document(),
            {"previous": current, "changedBy": uid, "changedAt": firestore.SERVER_TIMESTAMP, "fields": sorted(changes)},
        )
        transaction.update(ref, {**changes, "updatedAt": firestore.SERVER_TIMESTAMP})
        transaction.set(
            activity_ref(patient_id),
            activity_entry(
                "medication.updated",
                uid,
                datetime.now(UTC),
                {"medicationId": med_id, "name": changes.get("name", current["name"]), "fields": sorted(changes)},
            ),
        )
        transaction.set(
            audit_ref(),
            audit_entry(uid, "medication.updated", f"patients/{patient_id}", {"medicationId": med_id, "fields": sorted(changes)}),
        )

    patients_service.run_transaction(_apply)
    return get_medication(patient_id, uid, med_id)


# ---------- Tomas ----------


def log_dose(patient_id: str, uid: str, med_id: str, body: DoseLogCreate) -> DoseLog:
    access = patients_service.get_access(patient_id, uid, "meds.administer")
    require_active_patient(access)
    med_snap = meds_collection(patient_id).document(med_id).get()
    if not med_snap.exists:
        raise AppError(status.HTTP_404_NOT_FOUND, "medication_not_found", "Medicamento no encontrado.")
    med = to_medication(med_snap.id, patient_id, med_snap.to_dict())
    if not med.active:
        raise AppError(status.HTTP_409_CONFLICT, "medication_inactive", "El medicamento está inactivo.")

    now = datetime.now(UTC)
    actual = body.actual_at or (now if body.status == "given" else None)
    if actual and actual > now + CLOCK_SKEW:
        raise unprocessable("future_time", "La hora de administración no puede estar en el futuro.")

    tz = patient_tz(access)
    if med.schedule_type == "fixed":
        if body.scheduled_at is None:
            raise unprocessable("scheduled_at_required", "Indica a qué toma programada corresponde el registro.")
        scheduled = body.scheduled_at.astimezone(UTC)
        day = local_date_of(scheduled, tz)
        in_range = med.start_date <= day and (med.end_date is None or day <= med.end_date)
        if not in_range or scheduled not in {o.at for o in occurrences_on(med.schedule, tz, day)}:
            raise unprocessable("not_scheduled", "No hay una toma programada de este medicamento en ese horario.")
        ref = logs_collection(patient_id).document(f"{med_id}_{occurrence_key(scheduled)}")
    else:
        if body.scheduled_at is not None:
            raise unprocessable("schedule_not_allowed", "Un medicamento 'si es necesario' no tiene tomas programadas.")
        if body.status != "given":
            raise unprocessable("invalid_status", "En 'si es necesario' solo se registran las tomas administradas.")
        scheduled = None
        ref = logs_collection(patient_id).document()

    data = {
        "medicationId": med_id,
        "medicationName": med.name,  # copia: si luego cambia el medicamento, el registro conserva lo que se dio
        "dose": med.dose,
        "scheduledAt": scheduled,
        "agendaAt": scheduled or actual,  # instante para ubicarla en la agenda del día
        "status": body.status,
        "actualAt": actual,
        "reason": (body.reason or "").strip() or None,
        "recordedBy": uid,
        "recordedAt": firestore.SERVER_TIMESTAMP,
        "history": [],
    }
    db = get_db()
    batch = db.batch()
    batch.create(ref, data)
    batch.set(
        activity_ref(patient_id),
        activity_entry(
            f"medication.{body.status}",
            uid,
            actual or scheduled,
            {"medicationId": med_id, "logId": ref.id, "name": med.name, "dose": med.dose, "scheduledAt": scheduled,
             "reason": data["reason"]},
        ),
    )
    already = AppError(
        status.HTTP_409_CONFLICT, "dose_already_recorded", "Esta toma ya fue registrada. Si hubo un error, corrígela."
    )
    try:
        batch.commit()
    except AlreadyExists:
        raise already
    except Aborted:
        # Con registros simultáneos de la misma toma Firestore puede abortar sin aplicar nada.
        if ref.get().exists:
            raise already
        raise patients_service.busy_error()
    return to_log(ref.id, ref.get().to_dict())


def correct_dose(patient_id: str, uid: str, log_id: str, body: DoseLogCorrection) -> DoseLog:
    """Corrige un registro. Puede hacerlo quien lo registró (si conserva meds.administer) o el dueño."""
    access = patients_service.get_access(patient_id, uid, "patient.view")
    require_active_patient(access)
    ref = logs_collection(patient_id).document(log_id)
    now = datetime.now(UTC)
    if body.actual_at and body.actual_at > now + CLOCK_SKEW:
        raise unprocessable("future_time", "La hora de administración no puede estar en el futuro.")

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        snap = ref.get(transaction=transaction)
        if not snap.exists:
            raise AppError(status.HTTP_404_NOT_FOUND, "dose_not_found", "Registro no encontrado.")
        current = snap.to_dict()
        is_author = current["recordedBy"] == uid and "meds.administer" in access.permissions
        if not (access.relation == "owner" or is_author):
            raise AppError(
                status.HTTP_403_FORBIDDEN, "forbidden", "Solo quien registró la toma o el responsable pueden corregirla."
            )
        if current["scheduledAt"] is None and body.status != "given":
            raise unprocessable("invalid_status", "En 'si es necesario' solo se registran las tomas administradas.")
        if body.status == "omitted":
            actual = None
        else:
            # "given" sin hora nueva conserva la registrada (o usa la actual); "delayed" siempre la trae.
            actual = body.actual_at or current.get("actualAt") or now
        previous = {k: current.get(k) for k in ("status", "actualAt", "reason", "recordedBy")}
        previous["replacedAt"] = now  # (SERVER_TIMESTAMP no se permite dentro de listas)
        previous["replacedBy"] = uid
        transaction.update(
            ref,
            {
                "status": body.status,
                "actualAt": actual,
                "agendaAt": current["scheduledAt"] or actual,
                "reason": (body.reason or "").strip() or None,
                "history": firestore.ArrayUnion([previous]),
            },
        )
        transaction.set(
            activity_ref(patient_id),
            activity_entry(
                "medication.dose_corrected",
                uid,
                now,
                {"medicationId": current["medicationId"], "logId": log_id, "name": current["medicationName"],
                 "from": current["status"], "to": body.status},
            ),
        )
        transaction.set(
            audit_ref(),
            audit_entry(uid, "medication.dose_corrected", f"patients/{patient_id}",
                        {"logId": log_id, "from": current["status"], "to": body.status}),
        )

    patients_service.run_transaction(_apply)
    return to_log(log_id, ref.get().to_dict())

