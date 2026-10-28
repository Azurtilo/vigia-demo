"""Eliminación de pacientes y de cuentas (spec 014, RF-019-26, RF-019-27, D-065, D-098).

Firestore no borra cientos de documentos en una transacción: el borrado avanza por partes y es
repetible; si se corta, volver a pedirlo termina lo que faltó. No queda ningún dato personal en
`privacyOperations` (solo tipo, conteos y fecha).
"""

from datetime import UTC, datetime, timedelta

from fastapi import status
from firebase_admin import auth
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db, init_firebase
from app.core.security import Identity
from app.services import edge_cache, push
from app.services.audit import write_audit
from app.services.patients import MEMBERSHIPS, PATIENTS, USERS, get_access

REAUTH_WINDOW = timedelta(minutes=5)
OPERATIONS = "privacyOperations"


def record_operation(kind: str, counts: dict) -> None:
    get_db().collection(OPERATIONS).add({"kind": kind, "counts": counts, "at": datetime.now(UTC)})


def _delete_query(query) -> int:
    deleted = 0
    for snapshot in query.stream():
        snapshot.reference.delete()
        deleted += 1
    return deleted


def _delete_key_prefix(collection: str, prefix: str) -> int:
    db = get_db()
    query = (
        db.collection(collection)
        .where(filter=FieldFilter("key", ">=", prefix))
        .where(filter=FieldFilter("key", "<", prefix + ""))
    )
    return _delete_query(query)


def erase_patient_rows(patient_id: str) -> dict:
    """Borra el paciente, todas sus subcolecciones y todo lo que lo referencia."""
    db = get_db()
    patient_ref = db.collection(PATIENTS).document(patient_id)
    snapshot = patient_ref.get()
    counts = {"observations": sum(1 for _ in patient_ref.collection("observations").stream())}
    for collection in ("edgeNodes", "invitations", MEMBERSHIPS, "reminderDeliveries"):
        _delete_query(db.collection(collection).where(filter=FieldFilter("patientId", "==", patient_id)))
    for prefix in (f"alert:{patient_id}/", f"reminder:{patient_id}/"):
        _delete_key_prefix(push.RECEIPTS, prefix)
    counts["documents"] = db.recursive_delete(patient_ref)  # incluye registros, alertas e historial
    if snapshot.exists and snapshot.get("status") == "active":
        db.collection(USERS).document(snapshot.get("ownerUid")).update({"activePatientCount": firestore.Increment(-1)})
    edge_cache.forget(patient_id=patient_id)
    return counts


def delete_patient(patient_id: str, uid: str, typed_name: str) -> dict:
    access = get_access(patient_id, uid)
    if access.relation != "owner":
        raise AppError(status.HTTP_403_FORBIDDEN, "owner_only", "Solo el responsable del paciente puede hacer esto.")
    if (typed_name or "").strip().casefold() != access.patient["displayName"].strip().casefold():
        raise AppError(status.HTTP_422_UNPROCESSABLE_CONTENT, "name_mismatch", "El nombre no coincide. No se eliminó nada.")
    counts = erase_patient_rows(patient_id)
    write_audit(uid, "patient.deleted", f"{PATIENTS}/{patient_id}")
    record_operation("delete_patient", counts)
    return {"deleted": True}


def erase_account(identity: Identity) -> dict:
    """Pide un inicio de sesión reciente: reemplaza la contraseña que pedía Django (D-098)."""
    now = datetime.now(UTC)
    if identity.auth_time is None or now - datetime.fromtimestamp(identity.auth_time, UTC) > REAUTH_WINDOW:
        raise AppError(
            status.HTTP_401_UNAUTHORIZED,
            "reauth_required",
            "Vuelve a iniciar sesión para confirmar la eliminación de tu cuenta. No se eliminó nada.",
        )
    db = get_db()
    uid = identity.uid
    memberships = list(db.collection(MEMBERSHIPS).where(filter=FieldFilter("uid", "==", uid)).stream())
    owned = [m.get("patientId") for m in memberships if m.get("relation") == "owner"]
    for patient_id in owned:  # D-065: los pacientes del titular se van con la cuenta
        erase_patient_rows(patient_id)
    for membership in memberships:
        if membership.get("patientId") not in owned:
            membership.reference.delete()
            edge_cache.forget(patient_id=membership.get("patientId"))
    _delete_query(db.collection(push.DEVICES).where(filter=FieldFilter("uid", "==", uid)))
    _delete_query(db.collection(push.RECEIPTS).where(filter=FieldFilter("uid", "==", uid)))
    if identity.email:
        pending = db.collection("invitations").where(filter=FieldFilter("email", "==", identity.email.lower()))
        _delete_query(pending)
    db.collection("subscriptions").document(uid).delete()
    user_ref = db.collection(USERS).document(uid)
    db.recursive_delete(user_ref.collection("policyAcceptances"))
    if user_ref.get().exists:
        # Queda solo para que los registros en pacientes ajenos conserven un autor (anónimo).
        user_ref.set({"displayName": "Cuenta eliminada", "email": None, "role": "client", "status": "deleted",
                      "activePatientCount": 0, "deletedAt": now})
    init_firebase()
    try:
        auth.delete_user(uid)
    except auth.UserNotFoundError:
        pass  # un reintento tras un corte: la cuenta ya no existía
    record_operation("delete_account", {"patients": len(owned)})
    return {"deleted": True}
