"""Recordatorios de cuidado por push desde el cron (RF-019-08, D-088).

Cada 5 minutos como máximo (el tick llega cada minuto) se buscan:
- tomas programadas de la última hora sin registro;
- relojes de cambio de posición que vencen en 10 minutos o ya vencieron.

Van al dueño y a los cuidadores con el permiso correspondiente, no a la familia invitada
(como en Django). El texto es genérico. Cada aviso se envía una vez: un recibo por dispositivo y,
cuando todos lo confirmaron, `reminderDeliveries/{paciente}_{clave}`. La app programa además
avisos locales de respaldo con la misma clave de toma `{medId}_{instanteUTC}` (D-089).
"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.firebase import get_db
from app.core.schedule import DEFAULT_TIME_ZONE, local_date_of, occurrence_key, occurrences_on
from app.services import push
from app.services.medications import logs_collection, to_medication
from app.services.patients import MEMBERSHIPS, PATIENTS, USERS
from app.services.timer import CARE_RELATIONS

REMIND_EVERY = timedelta(minutes=5)
WINDOW = timedelta(hours=1)
POSTURE_SOON = timedelta(minutes=10)
CARE_TEXT = "Tienes un cuidado pendiente. Abre VIGIA para revisarlo."
DELIVERIES = "reminderDeliveries"

_last_run: datetime | None = None


def _care_recipients(patient_id: str, permission: str) -> list[str]:
    db = get_db()
    members = db.collection(MEMBERSHIPS).where(filter=FieldFilter("patientId", "==", patient_id)).stream()
    uids = [
        m.get("uid")
        for m in members
        if m.get("relation") in CARE_RELATIONS and permission in (m.to_dict().get("permissions") or [])
    ]
    users = db.get_all([db.collection(USERS).document(uid) for uid in uids]) if uids else []
    return [u.id for u in users if u.exists and u.get("status") == "active"]


def _active_patients(ids: set[str]) -> dict[str, dict]:
    db = get_db()
    found = db.get_all([db.collection(PATIENTS).document(pid) for pid in ids]) if ids else []
    return {p.id: p.to_dict() for p in found if p.exists and p.get("status") == "active"}


def due_doses(now: datetime) -> list[tuple[str, str]]:
    """(paciente, clave de toma) de las tomas de la última hora que nadie registró."""
    meds = list(get_db().collection_group("medications").where(filter=FieldFilter("active", "==", True)).stream())
    patients = _active_patients({m.reference.parent.parent.id for m in meds})
    due = []
    for snapshot in meds:
        patient_id = snapshot.reference.parent.parent.id
        if patient_id not in patients:
            continue
        med = to_medication(snapshot.id, patient_id, snapshot.to_dict())
        if med.schedule_type != "fixed" or med.schedule is None:
            continue
        tz = ZoneInfo(patients[patient_id].get("timeZone", DEFAULT_TIME_ZONE))
        for day in sorted({local_date_of(now - WINDOW, tz), local_date_of(now, tz)}):
            if day < med.start_date or (med.end_date is not None and day > med.end_date):
                continue
            for occurrence in occurrences_on(med.schedule, tz, day):
                if now - WINDOW <= occurrence.at <= now:
                    key = f"{med.id}_{occurrence_key(occurrence.at)}"
                    if not logs_collection(patient_id).document(key).get().exists:
                        due.append((patient_id, key))
    return due


def due_posture(now: datetime) -> list[tuple[str, str]]:
    """(paciente, clave) de relojes que vencen pronto ("soon") o ya vencieron ("due")."""
    timers = [t for t in get_db().collection_group("timer").stream() if t.id == "current"]
    patients = _active_patients({t.reference.parent.parent.id for t in timers})
    due = []
    for snapshot in timers:
        patient_id, d = snapshot.reference.parent.parent.id, snapshot.to_dict()
        if patient_id not in patients or d.get("paused") or not d.get("nextDueAt"):
            continue
        left = d["nextDueAt"] - now
        if left <= POSTURE_SOON and d["nextDueAt"] >= now - WINDOW:
            due.append((patient_id, f"posture_{d['generation']}_{'due' if left <= timedelta() else 'soon'}"))
    return due


def _deliver(patient_id: str, key: str, permission: str, posture: bool) -> bool:
    marker = get_db().collection(DELIVERIES).document(f"{patient_id}_{key}")
    if marker.get().exists:
        return False
    failed = False
    for device_id, device in push.active_devices(_care_recipients(patient_id, permission)):
        if posture and device.get("localPostureReminders"):
            continue  # ese teléfono ya programa el aviso del reloj
        failed = failed or push.deliver(device_id, device, f"reminder:{patient_id}/{key}", CARE_TEXT) is False
    if failed:
        return False  # el siguiente ciclo reintenta solo los dispositivos que fallaron
    marker.set({"patientId": patient_id, "key": key, "sentAt": datetime.now(UTC)})
    return True


def run(now: datetime | None = None, force: bool = False) -> int:
    """Envía los recordatorios pendientes. Devuelve cuántos quedaron enviados en esta pasada."""
    global _last_run
    now = now or datetime.now(UTC)
    if not push.enabled() or (not force and _last_run and now - _last_run < REMIND_EVERY):
        return 0
    _last_run = now
    sent = sum(_deliver(pid, key, "meds.administer", False) for pid, key in due_doses(now))
    sent += sum(_deliver(pid, key, "care.record", True) for pid, key in due_posture(now))
    return sent
