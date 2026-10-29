"""Endpoints de miembros e invitaciones. Toda la autorización ocurre en app.services.memberships."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.config import get_settings
from app.core.security import Identity, get_current_user, get_identity
from app.models.membership import (
    AcceptInvitation,
    Invitation,
    InvitationCreate,
    InvitationCreated,
    Member,
    MemberUpdate,
)
from app.models.patient import Patient
from app.models.user import UserProfile
from app.services import memberships as memberships_service

router = APIRouter(tags=["miembros e invitaciones"])

CurrentUser = Annotated[UserProfile, Depends(get_current_user)]

_errors = {
    401: {"description": "Sin sesión o sesión inválida"},
    403: {"description": "Sin permiso o acción exclusiva del responsable (`owner_only`)"},
    404: {"description": "Paciente, miembro o invitación no encontrados"},
    409: {"description": "Conflicto de estado (ver `error.code`)"},
}


# ---------- Invitaciones (responsable) ----------


@router.post(
    "/patients/{patient_id}/invitations",
    response_model=InvitationCreated,
    status_code=status.HTTP_201_CREATED,
    responses=_errors,
)
def create_invitation(patient_id: str, body: InvitationCreate, user: CurrentUser) -> InvitationCreated:
    """Crea una invitación de un solo uso, válida por 7 días.

    El `code` se devuelve **solo esta vez**: compártelo con la persona invitada (el MVP no envía correos).
    Si no envías `permissions`, se usan los permisos por defecto de la relación.
    """
    return memberships_service.create_invitation(patient_id, user.uid, user.email, body)


@router.get("/patients/{patient_id}/invitations", response_model=list[Invitation], responses=_errors)
def list_invitations(patient_id: str, user: CurrentUser) -> list[Invitation]:
    """Invitaciones del paciente (sin códigos). Solo el responsable."""
    return memberships_service.list_invitations(patient_id, user.uid)


@router.delete("/patients/{patient_id}/invitations/{invitation_id}", response_model=Invitation, responses=_errors)
def revoke_invitation(patient_id: str, invitation_id: str, user: CurrentUser) -> Invitation:
    """Anula una invitación pendiente. Solo el responsable."""
    return memberships_service.revoke_invitation(patient_id, user.uid, invitation_id)


# ---------- Aceptar (persona invitada) ----------


@router.post(
    "/invitations/accept",
    response_model=Patient,
    responses={**_errors, 410: {"description": "Invitación vencida"}},
)
def accept_invitation(
    body: AcceptInvitation,
    user: CurrentUser,
    identity: Annotated[Identity, Depends(get_identity)],
) -> Patient:
    """Acepta una invitación con su código. El correo de tu cuenta debe coincidir con el invitado.

    En producción se exige además que el correo esté verificado.
    """
    require_verified = get_settings().environment == "production"
    return memberships_service.accept_invitation(
        user.uid, user.email, identity.email_verified, require_verified, body.code
    )


# ---------- Miembros ----------


@router.get("/patients/{patient_id}/members", response_model=list[Member], responses=_errors)
def list_members(patient_id: str, user: CurrentUser) -> list[Member]:
    """Personas con acceso al paciente, su relación y permisos. Visible para todos los miembros."""
    return memberships_service.list_members(patient_id, user.uid)


@router.patch("/patients/{patient_id}/members/{member_uid}", response_model=Member, responses=_errors)
def update_member(patient_id: str, member_uid: str, body: MemberUpdate, user: CurrentUser) -> Member:
    """Reemplaza los permisos de un familiar o cuidador. Solo el responsable."""
    return memberships_service.update_member(patient_id, user.uid, member_uid, body)


@router.delete(
    "/patients/{patient_id}/members/{member_uid}", status_code=status.HTTP_204_NO_CONTENT, responses=_errors
)
def remove_member(patient_id: str, member_uid: str, user: CurrentUser) -> Response:
    """El responsable quita a un miembro, o un miembro se retira a sí mismo (usa tu propio uid)."""
    memberships_service.remove_member(patient_id, user.uid, member_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
