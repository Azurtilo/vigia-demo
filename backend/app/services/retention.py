"""Plazos de conservación de D-064 y purga diaria (spec 014, RF-019-24).

Mientras un paciente está activo se conservan sus registros de cuidado: son la trazabilidad
del cuidado delegado (HU-03, HU-06). Los intentos de código de D-064 no existen en este backend
(no los guarda), así que no tienen nada que purgar.
"""

from datetime import UTC, date, datetime, timedelta

from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.firebase import get_db
from app.services import push
from app.services.erase import erase_patient_rows, record_operation
from app.services.patients import PATIENTS

RETENTION = {
    "closed_invitations": timedelta(days=90),
    "reminder_receipts": timedelta(days=30),
    "push_receipts": timedelta(days=30),
    "observations_without_risk": timedelta(days=30),
    "observations_with_risk": timedelta(days=365),
    "alerts": timedelta(days=365),  # siguen a su observación con riesgo
    "archived_patients": timedelta(days=730),
}

_last_day: date | None = None


def _older(collection, field: str, limit: datetime):
    return collection.where(filter=FieldFilter(field, "<", limit)).stream()


def purge(now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    limit = {key: now - period for key, period in RETENTION.items()}
    db = get_db()
    counts = dict.fromkeys(RETENTION, 0)

    # Una invitación vence a los 7 días: si venció hace más de 90, también se cerró hace más de 90.
    for s in _older(db.collection("invitations"), "expiresAt", limit["closed_invitations"]):
        s.reference.delete()
        counts["closed_invitations"] += 1
    for s in _older(db.collection("reminderDeliveries"), "sentAt", limit["reminder_receipts"]):
        s.reference.delete()
        counts["reminder_receipts"] += 1
    for s in _older(db.collection(push.RECEIPTS), "reservedAt", limit["push_receipts"]):
        s.reference.delete()
        counts["push_receipts"] += 1
    for s in _older(db.collection_group("observations"), "observedAt", limit["observations_without_risk"]):
        if not s.get("risk"):
            counts["observations_without_risk"] += 1
        elif s.get("observedAt") < limit["observations_with_risk"]:
            counts["observations_with_risk"] += 1
        else:
            continue
        s.reference.delete()
    for s in _older(db.collection_group("alerts"), "occurredAt", limit["alerts"]):
        s.reference.delete()
        counts["alerts"] += 1
    archived = db.collection(PATIENTS).where(filter=FieldFilter("status", "==", "archived")).stream()
    for s in archived:
        since = s.to_dict().get("archivedAt") or s.to_dict().get("updatedAt")
        if since and since < limit["archived_patients"]:
            erase_patient_rows(s.id)
            counts["archived_patients"] += 1
    record_operation("purge", counts)
    return counts


def run_daily(now: datetime | None = None) -> dict | None:
    """Una purga por día desde el tick. Tras un reinicio puede repetirse ese día: es inofensivo."""
    global _last_day
    now = now or datetime.now(UTC)
    if _last_day == now.date():
        return None
    _last_day = now.date()
    return purge(now)
