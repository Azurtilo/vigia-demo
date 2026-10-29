"""Miembros de un paciente e invitaciones.

El código de invitación se entrega una sola vez; en Firestore solo se guarda su huella SHA-256,
que además es el ID del documento (aceptar = 1 lectura directa, sin consultas).
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import status
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.core.permissions import DEFAULT_PERMISSIONS
from app.models.membership import (
    Invitation,
    InvitationCreate,
    InvitationCreated,
    Member,
    MemberUpdate,
)
from app.services import patients as patients_service
from app.services.audit import audit_entry, audit_ref
from app.services.patients import MEMBERSHIPS, PATIENTS, USERS, membership_id

INVITATIONS = "invitations"
INVITATION_TTL = timedelta(days=7)
MAX_PENDING_PER_PATIENT = 20
# Sin caracteres ambiguos (0/O, 1/I/L): fácil de dictar o copiar. 31^20 ≈ 10^29 combinaciones.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def _new_code() -> str:
    raw = "".join(secrets.choice(_ALPHABET) for _ in range(20))
    return "-".join(raw[i : i + 4] for i in range(0, 20, 4))


def _normalize(code: str) -> str:
    return "".join(ch for ch in code.upper() if ch.isalnum())


def _hash(code: str) -> str:
    return hashlib.sha256(_normalize(code).encode()).hexdigest()


def _error(http_status: int, code: str, message: str) -> AppError:
    return AppError(http_status, code, message)


def _to_invitation(doc_id: str, data: dict) -> Invitation:
    status_ = data["status"]
    if status_ == "pending" and data["expiresAt"] <= datetime.now(UTC):
        status_ = "expired"
    return Invitation(
        id=doc_id,
        patient_id=data["patientId"],
        email=data["email"],
        relation=data["relation"],
        permissions=data["permissions"],
        status=status_,
        created_at=data.get("createdAt"),
        expires_at=data["expiresAt"],
    )


def _owner_access(patient_id: str, uid: str) -> patients_service.Access:
    access = patients_service.get_access(patient_id, uid)
    if access.relation != "owner":
        raise _error(status.HTTP_403_FORBIDDEN, "owner_only", "Solo el responsable del paciente puede hacer esto.")
    return access


# ---------- Invitaciones ----------


def create_invitation(patient_id: str, owner_uid: str, owner_email: str | None, body: InvitationCreate) -> InvitationCreated:
    access = _owner_access(patient_id, owner_uid)
    if access.patient["status"] != "active":
        raise _error(status.HTTP_409_CONFLICT, "patient_archived", "No se puede invitar a un paciente archivado.")
    email = body.email.lower()
    if owner_email and email == owner_email.lower():
        raise _error(status.HTTP_409_CONFLICT, "cannot_invite_self", "No puedes invitarte a ti mismo.")

    db = get_db()
    pending = (
        db.collection(INVITATIONS)
        .where(filter=FieldFilter("patientId", "==", patient_id))
        .where(filter=FieldFilter("status", "==", "pending"))
        .count()
        .get()[0][0]
        .value
    )
    if pending >= MAX_PENDING_PER_PATIENT:
        raise _error(
            status.HTTP_409_CONFLICT,
            "too_many_invitations",
            f"Hay {pending} invitaciones pendientes. Revoca alguna antes de crear otra.",
        )

    code = _new_code()
    ref = db.collection(INVITATIONS).document(_hash(code))
    data = {
        "patientId": patient_id,
        "email": email,
        "relation": body.relation,
        "permissions": list(body.permissions or DEFAULT_PERMISSIONS[body.relation]),
        "status": "pending",
        "createdBy": owner_uid,
        "createdAt": datetime.now(UTC),
        "expiresAt": datetime.now(UTC) + INVITATION_TTL,
    }
    batch = db.batch()
    batch.create(ref, data)
    # Auditoría sin el correo invitado (dato personal): basta con el ID y la relación.
    batch.set(
        audit_ref(),
        audit_entry(owner_uid, "invitation.created", f"patients/{patient_id}", {"invitationId": ref.id, "relation": body.relation}),
    )
    batch.commit()
    return InvitationCreated(invitation=_to_invitation(ref.id, data), code=code)


def list_invitations(patient_id: str, owner_uid: str) -> list[Invitation]:
    _owner_access(patient_id, owner_uid)
    docs = get_db().collection(INVITATIONS).where(filter=FieldFilter("patientId", "==", patient_id)).stream()
    invitations = [_to_invitation(d.id, d.to_dict()) for d in docs]
    return sorted(invitations, key=lambda i: i.expires_at, reverse=True)


def revoke_invitation(patient_id: str, owner_uid: str, invitation_id: str) -> Invitation:
    _owner_access(patient_id, owner_uid)
    db = get_db()
    ref = db.collection(INVITATIONS).document(invitation_id)

    @firestore.transactional
    def _revoke(transaction: firestore.Transaction) -> dict:
        snap = ref.get(transaction=transaction)
        if not snap.exists or snap.get("patientId") != patient_id:
            raise _error(status.HTTP_404_NOT_FOUND, "invitation_not_found", "Invitación no encontrada.")
        data = snap.to_dict()
        if data["status"] != "pending":
            raise _error(status.HTTP_409_CONFLICT, "invitation_not_pending", "La invitación ya no está pendiente.")
        transaction.update(ref, {"status": "revoked", "revokedAt": firestore.SERVER_TIMESTAMP})
        transaction.set(
            audit_ref(),
            audit_entry(owner_uid, "invitation.revoked", f"patients/{patient_id}", {"invitationId": invitation_id}),
        )
        return {**data, "status": "revoked"}

    data = patients_service.run_transaction(_revoke)
    return _to_invitation(invitation_id, data)


def accept_invitation(uid: str, email: str | None, email_verified: bool, require_verified: bool, code: str):
    """Crea la membresía si el código es válido, vigente, pendiente y dirigido al correo de quien acepta."""
    if require_verified and not email_verified:
        raise _error(status.HTTP_403_FORBIDDEN, "email_not_verified", "Verifica tu correo antes de aceptar invitaciones.")
    db = get_db()
    ref = db.collection(INVITATIONS).document(_hash(code))

    @firestore.transactional
    def _accept(transaction: firestore.Transaction) -> str:
        snap = ref.get(transaction=transaction)
        if not snap.exists:
            raise _error(status.HTTP_404_NOT_FOUND, "invitation_invalid", "El código de invitación no es válido.")
        inv = snap.to_dict()
        if inv["status"] == "accepted":
            raise _error(status.HTTP_409_CONFLICT, "invitation_used", "Esta invitación ya fue utilizada.")
        if inv["status"] == "revoked":
            raise _error(status.HTTP_409_CONFLICT, "invitation_revoked", "Esta invitación fue anulada por el responsable.")
        if inv["expiresAt"] <= datetime.now(UTC):
            raise _error(status.HTTP_410_GONE, "invitation_expired", "Esta invitación venció. Pide una nueva.")
        if not email or email.lower() != inv["email"]:
            # No se revela a qué correo fue enviada.
            raise _error(
                status.HTTP_403_FORBIDDEN, "invitation_email_mismatch", "Esta invitación fue enviada a otro correo."
            )
        patient_id = inv["patientId"]
        patient = db.collection(PATIENTS).document(patient_id).get(transaction=transaction)
        if not patient.exists or patient.get("status") != "active":
            raise _error(status.HTTP_409_CONFLICT, "patient_archived", "El paciente de esta invitación no está activo.")
        member_ref = db.collection(MEMBERSHIPS).document(membership_id(patient_id, uid))
        if member_ref.get(transaction=transaction).exists:
            raise _error(status.HTTP_409_CONFLICT, "already_member", "Ya tienes acceso a este paciente.")
        transaction.create(
            member_ref,
            {
                "patientId": patient_id,
                "uid": uid,
                "relation": inv["relation"],
                "permissions": inv["permissions"],
                "invitationId": ref.id,
                "createdAt": firestore.SERVER_TIMESTAMP,
            },
        )
        transaction.update(ref, {"status": "accepted", "acceptedBy": uid, "acceptedAt": firestore.SERVER_TIMESTAMP})
        transaction.set(
            audit_ref(),
            audit_entry(uid, "membership.joined", f"patients/{patient_id}", {"invitationId": ref.id, "relation": inv["relation"]}),
        )
        return patient_id

    patient_id = patients_service.run_transaction(_accept)
    return patients_service.get_patient(patient_id, uid)


# ---------- Miembros ----------


def list_members(patient_id: str, uid: str) -> list[Member]:
    """Visible para cualquier miembro con patient.view. Sin correos (minimización de datos)."""
    patients_service.get_access(patient_id, uid, "patient.view")
    db = get_db()
    members = [m.to_dict() for m in db.collection(MEMBERSHIPS).where(filter=FieldFilter("patientId", "==", patient_id)).stream()]
    users = {s.id: s.to_dict() for s in db.get_all([db.collection(USERS).document(m["uid"]) for m in members]) if s.exists}
    order = {"owner": 0, "family": 1, "caregiver": 2}
    result = [
        Member(
            uid=m["uid"],
            display_name=users.get(m["uid"], {}).get("displayName", "(cuenta eliminada)"),
            relation=m["relation"],
            permissions=m["permissions"],
        )
        for m in members
    ]
    return sorted(result, key=lambda m: (order[m.relation], m.display_name.lower()))


def update_member(patient_id: str, owner_uid: str, member_uid: str, body: MemberUpdate) -> Member:
    _owner_access(patient_id, owner_uid)
    db = get_db()
    ref = db.collection(MEMBERSHIPS).document(membership_id(patient_id, member_uid))

    @firestore.transactional
    def _update(transaction: firestore.Transaction) -> dict:
        snap = ref.get(transaction=transaction)
        if not snap.exists:
            raise _error(status.HTTP_404_NOT_FOUND, "member_not_found", "Esa persona no es miembro de este paciente.")
        data = snap.to_dict()
        if data["relation"] == "owner":
            raise _error(status.HTTP_409_CONFLICT, "owner_permissions_fixed", "Los permisos del responsable no se modifican.")
        transaction.update(ref, {"permissions": body.permissions, "updatedAt": firestore.SERVER_TIMESTAMP})
        transaction.set(
            audit_ref(),
            audit_entry(
                owner_uid,
                "membership.permissions_changed",
                f"patients/{patient_id}",
                {"member": member_uid, "from": sorted(data["permissions"]), "to": body.permissions},
            ),
        )
        return {**data, "permissions": body.permissions}

    data = patients_service.run_transaction(_update)
    user = db.collection(USERS).document(member_uid).get()
    return Member(
        uid=member_uid,
        display_name=user.get("displayName") if user.exists else "(cuenta eliminada)",
        relation=data["relation"],
        permissions=data["permissions"],
    )


def remove_member(patient_id: str, actor_uid: str, member_uid: str) -> None:
    """El dueño puede quitar a cualquier miembro; un miembro puede retirarse a sí mismo."""
    access = patients_service.get_access(patient_id, actor_uid)
    leaving = actor_uid == member_uid
    if leaving and access.relation == "owner":
        raise _error(
            status.HTTP_409_CONFLICT, "owner_cannot_leave", "El responsable no puede retirarse; puede archivar al paciente."
        )
    if not leaving and access.relation != "owner":
        raise _error(status.HTTP_403_FORBIDDEN, "owner_only", "Solo el responsable del paciente puede hacer esto.")
    db = get_db()
    ref = db.collection(MEMBERSHIPS).document(membership_id(patient_id, member_uid))
    snap = ref.get()
    if not snap.exists:
        raise _error(status.HTTP_404_NOT_FOUND, "member_not_found", "Esa persona no es miembro de este paciente.")
    batch = db.batch()
    batch.delete(ref)
    batch.set(
        audit_ref(),
        audit_entry(
            actor_uid,
            "membership.left" if leaving else "membership.removed",
            f"patients/{patient_id}",
            {"member": member_uid, "relation": snap.get("relation")},
        ),
    )
    batch.commit()
