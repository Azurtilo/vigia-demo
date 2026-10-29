"""Reglas de negocio de pacientes: acceso por membresía, límite de plan y archivo."""

import random
import time
from dataclasses import dataclass

from fastapi import status
from google.api_core.exceptions import Aborted
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.core.permissions import DEFAULT_PERMISSIONS, Permission, Relation
from app.core.schedule import DEFAULT_TIME_ZONE
from app.models.patient import Patient, PatientCreate, PatientStatus, PatientUpdate, PlanUsage
from app.services import edge_cache, plans
from app.services.audit import audit_entry, audit_ref

PATIENTS = "patients"
MEMBERSHIPS = "memberships"
USERS = "users"

_NOT_FOUND = AppError(status.HTTP_404_NOT_FOUND, "patient_not_found", "Paciente no encontrado.")


@dataclass(frozen=True)
class Access:
    patient: dict
    patient_id: str
    relation: Relation
    permissions: tuple[Permission, ...]


def membership_id(patient_id: str, uid: str) -> str:
    return f"{patient_id}_{uid}"


def busy_error() -> AppError:
    return AppError(
        status.HTTP_503_SERVICE_UNAVAILABLE, "service_busy", "Hay muchas solicitudes a la vez. Intenta nuevamente."
    )


def _limit_error(plan: dict) -> AppError:
    return AppError(
        status.HTTP_403_FORBIDDEN,
        "plan_limit_reached",
        f"Tu plan {plan['name']} permite hasta {plan['maxPatients']} paciente(s) activo(s). "
        "Archiva un paciente o cambia de plan para agregar otro.",
    )


def _to_patient(patient_id: str, data: dict, relation: Relation, permissions: tuple[Permission, ...]) -> Patient:
    return Patient(
        id=patient_id,
        owner_uid=data["ownerUid"],
        display_name=data["displayName"],
        time_zone=data.get("timeZone", DEFAULT_TIME_ZONE),
        status=data["status"],
        birth_date=data.get("birthDate"),
        mobility=data.get("mobility"),
        care_needs=data.get("careNeeds"),
        allergies=data.get("allergies", []),
        notes=data.get("notes"),
        emergency_contacts=data.get("emergencyContacts", []),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
        my_relation=relation,
        my_permissions=list(permissions),
    )


def _to_firestore(fields: dict) -> dict:
    """Convierte campos del modelo (snake_case) al formato guardado (camelCase; fechas como texto ISO)."""
    names = {
        "display_name": "displayName",
        "time_zone": "timeZone",
        "birth_date": "birthDate",
        "care_needs": "careNeeds",
        "emergency_contacts": "emergencyContacts",
    }
    out = {}
    for key, value in fields.items():
        if key == "birth_date" and value is not None:
            value = value.isoformat()  # Firestore no tiene tipo "fecha sin hora"
        if key == "emergency_contacts" and value is not None:
            value = [{k: v for k, v in c.items() if v is not None} for c in value]
        out[names.get(key, key)] = value
    return out


# ---------- Acceso ----------


def get_access(patient_id: str, uid: str, required: Permission | None = None) -> Access:
    """Verifica que `uid` tenga relación con el paciente y, si se pide, un permiso concreto.

    Sin relación se responde 404 (no 403) para no revelar si el paciente existe.
    """
    db = get_db()
    membership = db.collection(MEMBERSHIPS).document(membership_id(patient_id, uid)).get()
    if not membership.exists:
        raise _NOT_FOUND
    patient = db.collection(PATIENTS).document(patient_id).get()
    if not patient.exists:
        raise _NOT_FOUND
    m = membership.to_dict()
    access = Access(patient.to_dict(), patient_id, m["relation"], tuple(m.get("permissions", [])))
    if required and required not in access.permissions:
        raise AppError(status.HTTP_403_FORBIDDEN, "forbidden", "No tienes permiso para esta acción.")
    return access


def _require_owner(access: Access) -> None:
    if access.relation != "owner":
        raise AppError(status.HTTP_403_FORBIDDEN, "owner_only", "Solo el responsable del paciente puede hacer esto.")


# ---------- Consultas ----------


def get_patient(patient_id: str, uid: str) -> Patient:
    access = get_access(patient_id, uid, "patient.view")
    return _to_patient(patient_id, access.patient, access.relation, access.permissions)


def list_patients(uid: str, status_filter: PatientStatus | None = "active") -> list[Patient]:
    """Pacientes con los que el usuario tiene relación: 1 consulta + 1 lectura por lote."""
    db = get_db()
    snapshots = db.collection(MEMBERSHIPS).where(filter=FieldFilter("uid", "==", uid)).stream()
    memberships = [m for m in (s.to_dict() for s in snapshots) if "patient.view" in m.get("permissions", [])]
    refs = [db.collection(PATIENTS).document(m["patientId"]) for m in memberships]
    by_id = {s.id: s.to_dict() for s in db.get_all(refs) if s.exists} if refs else {}
    result = [
        _to_patient(m["patientId"], by_id[m["patientId"]], m["relation"], tuple(m["permissions"]))
        for m in memberships
        if m["patientId"] in by_id and (status_filter is None or by_id[m["patientId"]]["status"] == status_filter)
    ]
    return sorted(result, key=lambda p: p.display_name.lower())


def plan_usage(uid: str) -> PlanUsage:
    plan_id, plan = plans.read_plan_for_user(uid)
    user = get_db().collection(USERS).document(uid).get()
    active = user.get("activePatientCount") if user.exists else 0
    limit = plan.get("maxPatients")
    return PlanUsage(
        plan_id=plan_id,
        plan_name=plan["name"],
        max_patients=limit,
        active_patients=active,
        can_add_patient=limit is None or active < limit,
    )


# ---------- Altas y cambios de estado (con límite de plan) ----------


def create_patient(uid: str, body: PatientCreate) -> Patient:
    db = get_db()
    user_ref = db.collection(USERS).document(uid)
    patient_ref = db.collection(PATIENTS).document()
    membership_ref = db.collection(MEMBERSHIPS).document(membership_id(patient_ref.id, uid))
    owner_permissions = DEFAULT_PERMISSIONS["owner"]

    @firestore.transactional
    def _create(transaction: firestore.Transaction) -> None:
        # Leer contador y plan DENTRO de la transacción: si otra solicitud simultánea crea un
        # paciente, Firestore detecta el conflicto y reintenta con el valor actualizado.
        active = user_ref.get(transaction=transaction).get("activePatientCount") or 0
        _, plan = plans.read_plan_for_user(uid, transaction)
        if plan.get("maxPatients") is not None and active >= plan["maxPatients"]:
            raise _limit_error(plan)
        transaction.create(
            patient_ref,
            {
                **_to_firestore(body.model_dump()),
                "ownerUid": uid,
                "status": "active",
                "activeCameraId": None,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            },
        )
        transaction.create(
            membership_ref,
            {
                "patientId": patient_ref.id,
                "uid": uid,
                "relation": "owner",
                "permissions": list(owner_permissions),
                "createdAt": firestore.SERVER_TIMESTAMP,
            },
        )
        transaction.update(user_ref, {"activePatientCount": firestore.Increment(1)})
        transaction.set(audit_ref(), audit_entry(uid, "patient.created", f"patients/{patient_ref.id}"))

    # Antes de cada intento, una lectura rápida sin bloqueos: si el cupo ya está lleno se informa
    # de inmediato, sin abrir una transacción que compita con otras. La transacción sigue siendo
    # la garantía real del límite. Si Firestore aborta por contención, se reintenta: casi siempre
    # otra solicitud simultánea ocupó el cupo y el reintento informa ese motivo real.
    for attempt in range(3):
        usage = plan_usage(uid)
        if not usage.can_add_patient:
            raise _limit_error({"name": usage.plan_name, "maxPatients": usage.max_patients})
        try:
            run_transaction(_create)
            break
        except AppError as exc:
            if exc.code != "service_busy" or attempt == 2:
                raise
            # Espera aleatoria (backoff con jitter): sin ella, los reintentos simultáneos vuelven a
            # bloquear el documento y la solicitud ganadora no alcanza a guardar.
            time.sleep(random.uniform(0.2, 0.6) * (attempt + 1))
    return get_patient(patient_ref.id, uid)


def set_patient_status(patient_id: str, uid: str, new_status: PatientStatus) -> Patient:
    """Archivar libera un cupo del plan; reactivar vuelve a exigirlo. Solo el dueño."""
    _require_owner(get_access(patient_id, uid))
    db = get_db()
    user_ref = db.collection(USERS).document(uid)
    patient_ref = db.collection(PATIENTS).document(patient_id)

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        current = patient_ref.get(transaction=transaction).get("status")
        active = user_ref.get(transaction=transaction).get("activePatientCount") or 0
        if current == new_status:
            raise AppError(
                status.HTTP_409_CONFLICT,
                f"already_{new_status}",
                "El paciente ya está archivado." if new_status == "archived" else "El paciente ya está activo.",
            )
        if new_status == "active":
            _, plan = plans.read_plan_for_user(uid, transaction)
            if plan.get("maxPatients") is not None and active >= plan["maxPatients"]:
                raise _limit_error(plan)
        transaction.update(
            patient_ref,
            {
                "status": new_status,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                # Desde cuándo está archivado: a los 2 años se purga (D-064, spec 019).
                "archivedAt": firestore.SERVER_TIMESTAMP if new_status == "archived" else None,
            },
        )
        transaction.update(
            user_ref, {"activePatientCount": firestore.Increment(1 if new_status == "active" else -1)}
        )
        action = "patient.reactivated" if new_status == "active" else "patient.archived"
        transaction.set(audit_ref(), audit_entry(uid, action, f"patients/{patient_id}"))

    run_transaction(_apply)
    edge_cache.forget(patient_id=patient_id)  # un paciente archivado no se monitorea
    return get_patient(patient_id, uid)


def update_patient(patient_id: str, uid: str, body: PatientUpdate) -> Patient:
    access = get_access(patient_id, uid, "patient.edit")
    if access.patient["status"] == "archived":
        raise AppError(status.HTTP_409_CONFLICT, "patient_archived", "Un paciente archivado no se puede editar.")
    changes = _to_firestore(body.model_dump(include=body.model_fields_set))
    if changes:
        db = get_db()
        batch = db.batch()
        batch.update(db.collection(PATIENTS).document(patient_id), {**changes, "updatedAt": firestore.SERVER_TIMESTAMP})
        # Se auditan los NOMBRES de los campos cambiados, no sus valores (pueden ser datos de salud).
        batch.set(
            audit_ref(),
            audit_entry(uid, "patient.updated", f"patients/{patient_id}", {"fields": sorted(changes)}),
        )
        batch.commit()
    return get_patient(patient_id, uid)


def run_transaction(transactional_fn):
    """Ejecuta una función @firestore.transactional y devuelve su resultado.

    Si Firestore la aborta por contención (tras sus propios reintentos), responde 503 reintentable.
    """
    try:
        return transactional_fn(get_db().transaction())
    except Aborted:
        raise busy_error()
    except ValueError as exc:
        # Al agotar los reintentos por contención, Firestore lanza ValueError causado por Aborted
        # (google/cloud/firestore_v1/transaction.py). No se aplicó ningún cambio.
        if isinstance(exc.__cause__, Aborted):
            raise busy_error() from exc
        raise
