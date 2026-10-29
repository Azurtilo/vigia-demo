"""Reloj de cambio de posición (HU-04, RF-019-06). Mismas reglas que la API Django (spec 011).

- El reloj se crea explícitamente: un cambio de posición no inventa un reloj que nadie pidió.
- Registrar un cambio de posición reinicia el intervalo desde la hora del cambio.
- `generation` evita que dos personas cambien el reloj a la vez sin ver el estado del otro.
- Requiere `care.record`, consentimiento de cuidado y la función `positionChanges` del plan del dueño.
"""

from datetime import UTC, datetime, timedelta

from fastapi import status
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.timer import TimerAction, TimerSchedule, TimerScheduleItem, TimerState
from app.services.care_common import require_active_patient, require_feature
from app.services.consent import require_care
from app.services.patients import MEMBERSHIPS, PATIENTS, get_access, run_transaction

POSITIONS = "positionChanges"
# Los recordatorios de cuidado van al dueño y a los cuidadores, no a la familia invitada (Django).
CARE_RELATIONS = ("owner", "caregiver")


def timer_ref(patient_id: str) -> firestore.DocumentReference:
    return get_db().collection(PATIENTS).document(patient_id).collection("timer").document("current")


def _conflict(code: str, message: str) -> AppError:
    return AppError(status.HTTP_409_CONFLICT, code, message)


def _to_state(d: dict | None) -> TimerState:
    if not d:
        return TimerState(exists=False)
    return TimerState(
        exists=True,
        interval_minutes=d["intervalMinutes"],
        anchor_at=d.get("anchorAt"),
        next_due_at=d.get("nextDueAt"),
        paused=d["paused"],
        generation=d["generation"],
        last_position_at=d.get("lastPositionAt"),
    )


def get_timer(patient_id: str, uid: str) -> TimerState:
    get_access(patient_id, uid, "patient.view")
    return _to_state(timer_ref(patient_id).get().to_dict())


def act(patient_id: str, uid: str, body: TimerAction) -> TimerState:
    access = get_access(patient_id, uid, "care.record")
    require_active_patient(access)
    require_care(access)
    require_feature(access, POSITIONS, "El reloj de cambios de posición")
    ref = timer_ref(patient_id)
    interval = timedelta(minutes=body.interval_minutes)

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> dict:
        snapshot = ref.get(transaction=transaction)
        now = datetime.now(UTC)
        if body.action == "start":
            if snapshot.exists or body.generation != 0:
                raise _conflict("timer_exists", "El reloj ya existe. Recarga para consultar su estado.")
            data = {
                "intervalMinutes": body.interval_minutes,
                "anchorAt": now,
                "nextDueAt": now + interval,
                "paused": False,
                "generation": 1,
                "lastPositionAt": None,
                "updatedBy": uid,
            }
            transaction.set(ref, data)
            return data
        if not snapshot.exists:
            # Estado vacío: solo "start" es válido.
            raise _conflict("timer_missing", "Aún no hay recordatorio. Crea uno primero.")
        d = snapshot.to_dict()
        if d["generation"] != body.generation:
            raise _conflict("timer_changed", "El reloj cambió. Recarga para ver su estado.")
        if body.action == "pause":
            d |= {"paused": True, "nextDueAt": None}
        elif body.action == "resume":
            if not d["paused"]:
                raise _conflict("timer_running", "El reloj ya está activo.")
            d |= {"paused": False, "anchorAt": now, "intervalMinutes": body.interval_minutes, "nextDueAt": now + interval}
        else:  # interval: se cuenta desde el último cambio de posición (o desde el inicio)
            anchor = d.get("lastPositionAt") or d["anchorAt"]
            d |= {
                "intervalMinutes": body.interval_minutes,
                "anchorAt": anchor,
                "nextDueAt": None if d["paused"] else anchor + interval,
            }
        d |= {"generation": d["generation"] + 1, "updatedBy": uid}
        transaction.set(ref, d)
        return d

    return _to_state(run_transaction(_apply))


def restart_after_position(patient_id: str, at: datetime, uid: str) -> None:
    """Reinicia el reloj tras un cambio de posición registrado (HU-04). Sin reloj, no hace nada."""
    ref = timer_ref(patient_id)

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        snapshot = ref.get(transaction=transaction)
        if not snapshot.exists:
            return
        d = snapshot.to_dict()
        if d.get("lastPositionAt") and at <= d["lastPositionAt"]:
            return  # un cambio registrado tarde no retrocede el reloj
        transaction.update(
            ref,
            {
                "anchorAt": at,
                "lastPositionAt": at,
                "nextDueAt": at + timedelta(minutes=d["intervalMinutes"]),
                "paused": False,
                "generation": d["generation"] + 1,
                "updatedBy": uid,
            },
        )

    run_transaction(_apply)


def schedule(uid: str) -> TimerSchedule:
    """Relojes activos para avisos locales: sin nombres ni datos clínicos (spec 011)."""
    db = get_db()
    memberships = db.collection(MEMBERSHIPS).where(filter=FieldFilter("uid", "==", uid)).stream()
    ids = [
        m.get("patientId")
        for m in memberships
        if m.get("relation") in CARE_RELATIONS and "care.record" in (m.to_dict().get("permissions") or [])
    ]
    patients = db.get_all([db.collection(PATIENTS).document(pid) for pid in ids]) if ids else []
    ids = [p.id for p in patients if p.exists and p.get("status") == "active"]
    items = []
    for snapshot in db.get_all([timer_ref(pid) for pid in ids]) if ids else []:
        d = snapshot.to_dict() if snapshot.exists else None
        if d and not d["paused"] and d.get("nextDueAt"):
            items.append(TimerScheduleItem(patient_id=snapshot.reference.parent.parent.id, generation=d["generation"], due=d["nextDueAt"]))
    return TimerSchedule(items=items, server_time=datetime.now(UTC))
