"""Política de privacidad y consentimiento del paciente por finalidad (spec 014, RF-019-07).

- La cuenta acepta la versión vigente de la política; la API la exige si `privacy_enforced`.
- `cuidado`: sin consentimiento activo, la ficha se lee pero no se registran datos nuevos (D-066).
- `deteccion`: falla cerrado siempre; sin consentimiento, el nodo recibe 403.
- Solo el dueño registra o revoca. Cada registro se conserva (con su revocación) en
  `consentRecords`; `consents/{finalidad}` apunta al vigente.
"""

from datetime import UTC, datetime
from typing import Literal

from fastapi import status
from google.cloud import firestore

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.privacy import ConsentCreate, PatientConsent, PatientConsents, PolicyStatus
from app.models.user import UserProfile
from app.services import edge_cache
from app.services.audit import audit_entry, audit_ref
from app.services.patients import PATIENTS, USERS, Access, get_access, run_transaction

Scope = Literal["cuidado", "deteccion"]
SCOPES: tuple[Scope, ...] = ("cuidado", "deteccion")
MISSING = {
    "cuidado": "Registra el consentimiento de datos de cuidado de este paciente antes de agregar registros.",
    "deteccion": "Registra el consentimiento de detección con cámara de este paciente antes de usarla.",
}


def consent_ref(patient_id: str, scope: Scope) -> firestore.DocumentReference:
    return get_db().collection(PATIENTS).document(patient_id).collection("consents").document(scope)


def is_active(patient_id: str, scope: Scope, transaction: firestore.Transaction | None = None) -> bool:
    snapshot = consent_ref(patient_id, scope).get(transaction=transaction)
    return snapshot.exists and snapshot.get("active") is True


def require_care(access: Access) -> None:
    """Datos de cuidado nuevos solo con consentimiento vigente (si la privacidad está activada)."""
    if get_settings().privacy_enforced and not is_active(access.patient_id, "cuidado"):
        raise AppError(status.HTTP_403_FORBIDDEN, "consent_required", MISSING["cuidado"])


# ---------- Política de la cuenta ----------


def policy_status(user: UserProfile) -> PolicyStatus:
    settings = get_settings()
    return PolicyStatus(
        policy_version=settings.privacy_policy_version,
        accepted=user.policy_accepted_version == settings.privacy_policy_version,
        accepted_version=user.policy_accepted_version,
        enforced=settings.privacy_enforced,
    )


def accept_policy(user: UserProfile) -> PolicyStatus:
    version = get_settings().privacy_policy_version
    if user.policy_accepted_version != version:
        db = get_db()
        user_ref = db.collection(USERS).document(user.uid)
        now = datetime.now(UTC)
        batch = db.batch()
        batch.update(user_ref, {"policyAcceptedVersion": version, "policyAcceptedAt": now})
        # Cada versión aceptada queda registrada (una vez por versión).
        batch.set(user_ref.collection("policyAcceptances").document(version), {"version": version, "acceptedAt": now})
        batch.commit()
        user = user.model_copy(update={"policy_accepted_version": version})
    return policy_status(user)


# ---------- Consentimiento del paciente ----------


def _owner_only(access: Access) -> None:
    if access.relation != "owner":
        raise AppError(status.HTTP_403_FORBIDDEN, "owner_only", "Solo el responsable del paciente puede hacer esto.")


def _to_consent(scope: Scope, d: dict | None) -> PatientConsent:
    if not d:
        return PatientConsent(scope=scope, active=False)
    return PatientConsent(
        scope=scope,
        active=d.get("active") is True,
        basis=d.get("basis"),
        representative_name=d.get("representativeName"),
        representative_relation=d.get("representativeRelation"),
        policy_version=d.get("policyVersion"),
        recorded_by=d.get("recordedBy"),
        recorded_at=d.get("recordedAt"),
        revoked_at=d.get("revokedAt"),
    )


def list_consents(patient_id: str, uid: str) -> PatientConsents:
    get_access(patient_id, uid, "patient.view")
    return PatientConsents(items=[_to_consent(s, consent_ref(patient_id, s).get().to_dict()) for s in SCOPES])


def register(patient_id: str, uid: str, body: ConsentCreate) -> PatientConsent:
    access = get_access(patient_id, uid)
    _owner_only(access)
    if access.patient["status"] != "active":
        raise AppError(status.HTTP_409_CONFLICT, "patient_archived", "Un paciente archivado es de solo lectura.")
    current_ref = consent_ref(patient_id, body.scope)
    record_ref = get_db().collection(PATIENTS).document(patient_id).collection("consentRecords").document()
    data = {
        "scope": body.scope,
        "active": True,
        "basis": body.basis,
        "representativeName": body.representative_name,
        "representativeRelation": body.representative_relation,
        "policyVersion": get_settings().privacy_policy_version,
        "recordedBy": uid,
        "recordedAt": datetime.now(UTC),
        "revokedAt": None,
    }

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        current = current_ref.get(transaction=transaction)
        if current.exists and current.get("active") is True:
            raise AppError(status.HTTP_409_CONFLICT, "consent_already_active", "Este consentimiento ya está registrado.")
        transaction.set(record_ref, data)
        transaction.set(current_ref, {**data, "recordId": record_ref.id})
        transaction.set(audit_ref(), audit_entry(uid, "consent.recorded", f"{PATIENTS}/{patient_id}", {"scope": body.scope}))

    run_transaction(_apply)
    if body.scope == "deteccion":
        edge_cache.forget(patient_id=patient_id)
    return _to_consent(body.scope, data)


def revoke(patient_id: str, uid: str, scope: Scope) -> PatientConsent:
    access = get_access(patient_id, uid)
    _owner_only(access)
    current_ref = consent_ref(patient_id, scope)
    now = datetime.now(UTC)

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> dict:
        current = current_ref.get(transaction=transaction)
        if not current.exists or current.get("active") is not True:
            raise AppError(status.HTTP_409_CONFLICT, "consent_not_active", "No hay un consentimiento vigente que revocar.")
        record_ref = get_db().collection(PATIENTS).document(patient_id).collection("consentRecords").document(current.get("recordId"))
        transaction.update(current_ref, {"active": False, "revokedAt": now})
        transaction.update(record_ref, {"active": False, "revokedAt": now})
        transaction.set(audit_ref(), audit_entry(uid, "consent.revoked", f"{PATIENTS}/{patient_id}", {"scope": scope}))
        return {**current.to_dict(), "active": False, "revokedAt": now}

    revoked = run_transaction(_apply)
    if scope == "deteccion":
        edge_cache.forget(patient_id=patient_id)  # el nodo se detiene al instante
    return _to_consent(scope, revoked)
