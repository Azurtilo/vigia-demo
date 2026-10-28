"""Exportación JSON de la cuenta y del paciente (spec 014, RF-019-25).

Nunca incluye tokens FCM, hashes de credenciales de nodos, códigos de invitación (el ID de una
invitación es la huella de su código) ni hashes de contenido.
"""

from datetime import UTC, date, datetime

from fastapi import status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.firebase import get_db
from app.services import push
from app.services.patients import MEMBERSHIPS, PATIENTS, USERS, get_access

SECRET_FIELDS = {"credentialHash", "token", "payloadHash"}
PATIENT_COLLECTIONS = (
    "medications",
    "medicationLogs",
    "careTasks",
    "taskLogs",
    "activity",
    "alerts",
    "observations",
    "consentRecords",
)


def plain(value):
    """Valores de Firestore a JSON, sin los campos secretos."""
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items() if k not in SECRET_FIELDS}
    if isinstance(value, list):
        return [plain(v) for v in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def _docs(query) -> list[dict]:
    return [{"id": s.id, **plain(s.to_dict())} for s in query.stream()]


def _envelope(kind: str) -> dict:
    return {
        "kind": kind,
        "exportedAt": datetime.now(UTC).isoformat(),
        "policyVersion": get_settings().privacy_policy_version,
    }


def patient_data(patient_id: str, uid: str) -> dict:
    """Todo lo del paciente. Solo el responsable."""
    access = get_access(patient_id, uid)
    if access.relation != "owner":
        raise AppError(status.HTTP_403_FORBIDDEN, "owner_only", "Solo el responsable del paciente puede hacer esto.")
    db = get_db()
    patient_ref = db.collection(PATIENTS).document(patient_id)
    data = {**_envelope("patient"), "patient": {"id": patient_id, **plain(access.patient)}}
    for name in PATIENT_COLLECTIONS:
        data[name] = _docs(patient_ref.collection(name))
    for med in data["medications"]:
        med["revisions"] = _docs(patient_ref.collection("medications").document(med["id"]).collection("revisions"))
    timer = patient_ref.collection("timer").document("current").get()
    data["timer"] = plain(timer.to_dict()) if timer.exists else None
    members = list(db.collection(MEMBERSHIPS).where(filter=FieldFilter("patientId", "==", patient_id)).stream())
    users = {u.id: u for u in db.get_all([db.collection(USERS).document(m.get("uid")) for m in members])} if members else {}
    data["members"] = [
        {
            "uid": m.get("uid"),
            "displayName": users[m.get("uid")].get("displayName") if users.get(m.get("uid")) and users[m.get("uid")].exists else None,
            "relation": m.get("relation"),
            "permissions": m.to_dict().get("permissions", []),
        }
        for m in members
    ]
    nodes = db.collection("edgeNodes").where(filter=FieldFilter("patientId", "==", patient_id)).stream()
    data["nodes"] = [plain(n.to_dict()) | {"id": n.id} for n in nodes]
    invitations = db.collection("invitations").where(filter=FieldFilter("patientId", "==", patient_id)).stream()
    data["invitations"] = [plain(i.to_dict()) for i in invitations]  # sin el ID: es la huella del código
    return data


def account_data(uid: str) -> dict:
    """La cuenta y lo que la persona registró en pacientes ajenos (no la ficha de esos pacientes)."""
    db = get_db()
    user_ref = db.collection(USERS).document(uid)
    user = user_ref.get()
    subscription = db.collection("subscriptions").document(uid).get()
    memberships = list(db.collection(MEMBERSHIPS).where(filter=FieldFilter("uid", "==", uid)).stream())
    others = [m.get("patientId") for m in memberships if m.get("relation") != "owner"]
    records = []
    for patient_id in others:
        patient_ref = db.collection(PATIENTS).document(patient_id)
        for collection, field in (("medicationLogs", "recordedBy"), ("taskLogs", "recordedBy"), ("alerts", "attendedBy")):
            for doc in _docs(patient_ref.collection(collection).where(filter=FieldFilter(field, "==", uid))):
                records.append({"patientId": patient_id, "collection": collection, **doc})
    devices = db.collection(push.DEVICES).where(filter=FieldFilter("uid", "==", uid)).stream()
    return {
        **_envelope("account"),
        "account": {"uid": uid, **plain(user.to_dict() or {})},
        "policyAcceptances": _docs(user_ref.collection("policyAcceptances")),
        "subscription": plain(subscription.to_dict()) if subscription.exists else None,
        "subscriptionChanges": _docs(db.collection("subscriptionChanges").where(filter=FieldFilter("uid", "==", uid))),
        "devices": [plain(d.to_dict()) for d in devices],  # sin el token
        "memberships": [
            {"patientId": m.get("patientId"), "relation": m.get("relation"), "permissions": m.to_dict().get("permissions", [])}
            for m in memberships
        ],
        "recordsInOtherPatients": records,
    }
