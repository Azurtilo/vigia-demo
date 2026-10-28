"""Plan de cuidados: tareas, su registro y cambios de posición.

Funciones según el plan del DUEÑO del paciente (features en la colección `plans`):
- `extendedCareTracking`: asignar responsable, marcar "no realizada" con motivo, agregar observaciones.
- `positionChanges`: tareas de cambio de posición y registro de posiciones.
"""

from datetime import UTC, date, datetime

from fastapi import status
from google.api_core.exceptions import Aborted, AlreadyExists
from google.cloud import firestore

from app.core.errors import AppError
from app.core.firebase import get_db
from app.core.schedule import local_date_of, occurrence_key, occurrences_on
from app.models.care import (
    CareTask,
    CareTaskCreate,
    CareTaskUpdate,
    PositionChangeCreate,
    TaskLog,
    TaskLogCorrection,
    TaskLogCreate,
)
from app.services import patients as patients_service
from app.services.activity import activity_entry, activity_ref
from app.services.audit import audit_entry, audit_ref
from app.services.care_common import (
    CLOCK_SKEW,
    patient_tz,
    require_active_patient,
    require_feature,
    schedule_from,
    schedule_to,
    unprocessable,
)

EXTENDED = "extendedCareTracking"
POSITIONS = "positionChanges"


def tasks_collection(patient_id: str) -> firestore.CollectionReference:
    return get_db().collection("patients").document(patient_id).collection("careTasks")


def task_logs_collection(patient_id: str) -> firestore.CollectionReference:
    return get_db().collection("patients").document(patient_id).collection("taskLogs")


def _not_found() -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "task_not_found", "Tarea no encontrada.")


# ---------- Conversión ----------


def to_task(task_id: str, patient_id: str, d: dict) -> CareTask:
    return CareTask(
        id=task_id,
        patient_id=patient_id,
        title=d["title"],
        description=d.get("description"),
        kind=d["kind"],
        schedule_type=d["scheduleType"],
        schedule=schedule_from(d.get("schedule")),
        start_date=date.fromisoformat(d["startDate"]),
        end_date=date.fromisoformat(d["endDate"]) if d.get("endDate") else None,
        assigned_to=d.get("assignedTo"),
        active=d["active"],
        created_by=d["createdBy"],
        created_at=d.get("createdAt"),
        updated_at=d.get("updatedAt"),
    )


def to_task_log(log_id: str, d: dict) -> TaskLog:
    return TaskLog(
        id=log_id,
        task_id=d.get("taskId"),
        title=d["title"],
        kind=d["kind"],
        scheduled_at=d.get("scheduledAt"),
        status=d["status"],
        done_at=d.get("doneAt"),
        reason=d.get("reason"),
        note=d.get("note"),
        position=d.get("position"),
        position_other=d.get("positionOther"),
        recorded_by=d["recordedBy"],
        recorded_at=d.get("recordedAt"),
        corrections=len(d.get("history", [])),
    )


def _task_fields(body: CareTaskCreate | CareTaskUpdate, only_sent: bool) -> dict:
    sent = body.model_fields_set if only_sent else set(type(body).model_fields)
    names = {
        "title": "title",
        "description": "description",
        "kind": "kind",
        "schedule_type": "scheduleType",
        "start_date": "startDate",
        "end_date": "endDate",
        "assigned_to": "assignedTo",
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


def _clean(text: str | None) -> str | None:
    return (text or "").strip() or None


# ---------- Reglas comunes ----------


def _check_assignee(patient_id: str, assignee: str | None) -> None:
    if assignee is None:
        return
    membership = get_db().collection("memberships").document(patients_service.membership_id(patient_id, assignee)).get()
    if not membership.exists:
        raise unprocessable("assignee_not_member", "El responsable asignado debe tener acceso a este paciente.")


def _check_log_features(access, kind: str, status_: str, note: str | None) -> None:
    if kind == "position_change":
        require_feature(access, POSITIONS, "El registro de cambios de posición")
    if status_ == "skipped":
        require_feature(access, EXTENDED, "Marcar una tarea como no realizada")
    if note:
        require_feature(access, EXTENDED, "Agregar observaciones")


def _check_position_for_kind(kind: str, status_: str, position: str | None) -> None:
    if kind == "position_change" and status_ == "done" and position is None:
        raise unprocessable("position_required", "Indica a qué posición se cambió al paciente.")
    if kind == "general" and position is not None:
        raise unprocessable("position_not_allowed", "Esta tarea no es de cambio de posición.")


def _validate_merged(d: dict) -> None:
    if d["scheduleType"] == "fixed" and not d.get("schedule"):
        raise unprocessable("schedule_required", "Una tarea con horario necesita al menos una hora.")
    if d["scheduleType"] == "unscheduled" and d.get("schedule"):
        raise unprocessable("schedule_not_allowed", "Una tarea sin horario no lleva horas.")
    if d.get("endDate") and d["endDate"] < d["startDate"]:
        raise unprocessable("invalid_dates", "La fecha de término no puede ser anterior a la de inicio.")


# ---------- Tareas ----------


def create_task(patient_id: str, uid: str, body: CareTaskCreate) -> CareTask:
    access = patients_service.get_access(patient_id, uid, "care.manage")
    require_active_patient(access)
    if body.kind == "position_change":
        require_feature(access, POSITIONS, "Las tareas de cambio de posición")
    if body.assigned_to:
        require_feature(access, EXTENDED, "Asignar un responsable")
        _check_assignee(patient_id, body.assigned_to)
    db = get_db()
    ref = tasks_collection(patient_id).document()
    batch = db.batch()
    batch.create(
        ref,
        {
            **_task_fields(body, only_sent=False),
            "active": True,
            "createdBy": uid,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        },
    )
    batch.set(
        activity_ref(patient_id),
        activity_entry("task.created", uid, datetime.now(UTC), {"taskId": ref.id, "title": body.title, "kind": body.kind}),
    )
    batch.set(audit_ref(), audit_entry(uid, "task.created", f"patients/{patient_id}", {"taskId": ref.id}))
    batch.commit()
    return get_task(patient_id, uid, ref.id)


def get_task(patient_id: str, uid: str, task_id: str) -> CareTask:
    patients_service.get_access(patient_id, uid, "patient.view")
    snap = tasks_collection(patient_id).document(task_id).get()
    if not snap.exists:
        raise _not_found()
    return to_task(snap.id, patient_id, snap.to_dict())


def list_tasks(patient_id: str, uid: str, include_inactive: bool) -> list[CareTask]:
    patients_service.get_access(patient_id, uid, "patient.view")
    tasks = [to_task(s.id, patient_id, s.to_dict()) for s in tasks_collection(patient_id).stream()]
    tasks = [t for t in tasks if include_inactive or t.active]
    return sorted(tasks, key=lambda t: (not t.active, t.title.lower()))


def update_task(patient_id: str, uid: str, task_id: str, body: CareTaskUpdate) -> CareTask:
    access = patients_service.get_access(patient_id, uid, "care.manage")
    require_active_patient(access)
    changes = _task_fields(body, only_sent=True)
    if not changes:
        return get_task(patient_id, uid, task_id)
    if any(changes[k] is None for k in {"title", "scheduleType", "startDate", "active"} & changes.keys()):
        raise unprocessable("validation_error", "Título, tipo de horario, inicio y estado no pueden quedar vacíos.")
    if changes.get("scheduleType") == "unscheduled" and "schedule" not in changes:
        changes["schedule"] = None
    if changes.get("assignedTo"):
        require_feature(access, EXTENDED, "Asignar un responsable")
        _check_assignee(patient_id, changes["assignedTo"])
    ref = tasks_collection(patient_id).document(task_id)

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        snap = ref.get(transaction=transaction)
        if not snap.exists:
            raise _not_found()
        current = snap.to_dict()
        _validate_merged({**current, **changes})
        transaction.update(ref, {**changes, "updatedAt": firestore.SERVER_TIMESTAMP})
        transaction.set(
            activity_ref(patient_id),
            activity_entry(
                "task.updated", uid, datetime.now(UTC),
                {"taskId": task_id, "title": changes.get("title", current["title"]), "fields": sorted(changes)},
            ),
        )
        transaction.set(
            audit_ref(),
            audit_entry(uid, "task.updated", f"patients/{patient_id}", {"taskId": task_id, "fields": sorted(changes)}),
        )

    patients_service.run_transaction(_apply)
    return get_task(patient_id, uid, task_id)


# ---------- Registro de tareas y posiciones ----------


def _commit_log(batch, ref, duplicate_message: str) -> None:
    already = AppError(status.HTTP_409_CONFLICT, "task_already_recorded", duplicate_message)
    try:
        batch.commit()
    except AlreadyExists:
        raise already
    except Aborted:
        if ref.get().exists:
            raise already
        raise patients_service.busy_error()


def _activity_type(kind: str, status_: str) -> str:
    return "position.changed" if kind == "position_change" and status_ == "done" else f"task.{status_}"


def log_task(patient_id: str, uid: str, task_id: str, body: TaskLogCreate) -> TaskLog:
    access = patients_service.get_access(patient_id, uid, "care.record")
    require_active_patient(access)
    snap = tasks_collection(patient_id).document(task_id).get()
    if not snap.exists:
        raise _not_found()
    task = to_task(snap.id, patient_id, snap.to_dict())
    if not task.active:
        raise AppError(status.HTTP_409_CONFLICT, "task_inactive", "La tarea está inactiva.")
    note = _clean(body.note)
    _check_log_features(access, task.kind, body.status, note)
    _check_position_for_kind(task.kind, body.status, body.position)

    now = datetime.now(UTC)
    done_at = body.done_at or (now if body.status == "done" else None)
    if done_at and done_at > now + CLOCK_SKEW:
        raise unprocessable("future_time", "La hora de realización no puede estar en el futuro.")

    tz = patient_tz(access)
    if task.schedule_type == "fixed":
        if body.scheduled_at is None:
            raise unprocessable("scheduled_at_required", "Indica a qué horario de la tarea corresponde el registro.")
        scheduled = body.scheduled_at.astimezone(UTC)
        day = local_date_of(scheduled, tz)
        in_range = task.start_date <= day and (task.end_date is None or day <= task.end_date)
        if not in_range or scheduled not in {o.at for o in occurrences_on(task.schedule, tz, day)}:
            raise unprocessable("not_scheduled", "La tarea no está programada en ese horario.")
        ref = task_logs_collection(patient_id).document(f"{task_id}_{occurrence_key(scheduled)}")
    else:
        if body.scheduled_at is not None:
            raise unprocessable("schedule_not_allowed", "Esta tarea no tiene horario.")
        if body.status != "done":
            raise unprocessable("invalid_status", "En tareas sin horario solo se registra lo realizado.")
        scheduled = None
        ref = task_logs_collection(patient_id).document()

    data = {
        "taskId": task_id,
        "title": task.title,  # copia: el registro conserva el nombre que tenía la tarea
        "kind": task.kind,
        "scheduledAt": scheduled,
        "agendaAt": scheduled or done_at,
        "status": body.status,
        "doneAt": done_at,
        "reason": _clean(body.reason),
        "note": note,
        "position": body.position,
        "positionOther": _clean(body.position_other),
        "recordedBy": uid,
        "recordedAt": firestore.SERVER_TIMESTAMP,
        "history": [],
    }
    batch = get_db().batch()
    batch.create(ref, data)
    batch.set(
        activity_ref(patient_id),
        activity_entry(
            _activity_type(task.kind, body.status), uid, done_at or scheduled,
            {"taskId": task_id, "logId": ref.id, "title": task.title, "position": body.position, "scheduledAt": scheduled,
             "reason": data["reason"], "note": data["note"]},
        ),
    )
    _commit_log(batch, ref, "Esta tarea ya fue registrada en ese horario. Si hubo un error, corrígela.")
    return to_task_log(ref.id, ref.get().to_dict())


def record_position_change(patient_id: str, uid: str, body: PositionChangeCreate) -> TaskLog:
    """Cambio de posición sin una tarea programada (p. ej. cuando el paciente lo necesitó)."""
    access = patients_service.get_access(patient_id, uid, "care.record")
    require_active_patient(access)
    note = _clean(body.note)
    require_feature(access, POSITIONS, "El registro de cambios de posición")
    if note:
        require_feature(access, EXTENDED, "Agregar observaciones")
    now = datetime.now(UTC)
    at = body.at or now
    if at > now + CLOCK_SKEW:
        raise unprocessable("future_time", "La hora no puede estar en el futuro.")
    ref = task_logs_collection(patient_id).document()
    data = {
        "taskId": None,
        "title": "Cambio de posición",
        "kind": "position_change",
        "scheduledAt": None,
        "agendaAt": at,
        "status": "done",
        "doneAt": at,
        "reason": None,
        "note": note,
        "position": body.position,
        "positionOther": _clean(body.position_other),
        "recordedBy": uid,
        "recordedAt": firestore.SERVER_TIMESTAMP,
        "history": [],
    }
    batch = get_db().batch()
    batch.create(ref, data)
    batch.set(
        activity_ref(patient_id),
        activity_entry("position.changed", uid, at, {"taskId": None, "logId": ref.id, "position": body.position}),
    )
    batch.commit()
    return to_task_log(ref.id, ref.get().to_dict())


def correct_task_log(patient_id: str, uid: str, log_id: str, body: TaskLogCorrection) -> TaskLog:
    """Corrige un registro. Quien lo registró (si conserva care.record) o el dueño. Guarda el valor anterior."""
    access = patients_service.get_access(patient_id, uid, "patient.view")
    require_active_patient(access)
    ref = task_logs_collection(patient_id).document(log_id)
    now = datetime.now(UTC)
    if body.done_at and body.done_at > now + CLOCK_SKEW:
        raise unprocessable("future_time", "La hora de realización no puede estar en el futuro.")
    note = _clean(body.note)

    current_snap = ref.get()
    if not current_snap.exists:
        raise AppError(status.HTTP_404_NOT_FOUND, "task_log_not_found", "Registro no encontrado.")
    current = current_snap.to_dict()
    is_author = current["recordedBy"] == uid and "care.record" in access.permissions
    if not (access.relation == "owner" or is_author):
        raise AppError(status.HTTP_403_FORBIDDEN, "forbidden", "Solo quien hizo el registro o el responsable pueden corregirlo.")
    _check_log_features(access, current["kind"], body.status, note)
    _check_position_for_kind(current["kind"], body.status, body.position)
    if current["scheduledAt"] is None and body.status != "done":
        raise unprocessable("invalid_status", "En tareas sin horario solo se registra lo realizado.")

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        latest = ref.get(transaction=transaction).to_dict()
        done_at = None if body.status == "skipped" else (body.done_at or latest.get("doneAt") or now)
        previous = {k: latest.get(k) for k in ("status", "doneAt", "reason", "note", "position", "positionOther", "recordedBy")}
        previous |= {"replacedAt": now, "replacedBy": uid}
        transaction.update(
            ref,
            {
                "status": body.status,
                "doneAt": done_at,
                "agendaAt": latest["scheduledAt"] or done_at,
                "reason": _clean(body.reason),
                "note": note,
                "position": body.position,
                "positionOther": _clean(body.position_other),
                "history": firestore.ArrayUnion([previous]),
            },
        )
        transaction.set(
            activity_ref(patient_id),
            activity_entry(
                "task.corrected", uid, now,
                {"taskId": latest.get("taskId"), "logId": log_id, "title": latest["title"], "from": latest["status"], "to": body.status},
            ),
        )
        transaction.set(
            audit_ref(),
            audit_entry(uid, "task.corrected", f"patients/{patient_id}", {"logId": log_id, "from": latest["status"], "to": body.status}),
        )

    patients_service.run_transaction(_apply)
    return to_task_log(log_id, ref.get().to_dict())
