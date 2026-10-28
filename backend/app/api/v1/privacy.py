"""Endpoints de política de privacidad y consentimiento del paciente. La autorización ocurre en app.services."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import get_current_user, get_registered_user
from app.models.privacy import ConsentCreate, PatientConsent, PatientConsents, PolicyStatus, Scope
from app.models.user import UserProfile
from app.services import consent as consent_service

router = APIRouter(tags=["privacidad"])

RegisteredUser = Annotated[UserProfile, Depends(get_registered_user)]
CurrentUser = Annotated[UserProfile, Depends(get_current_user)]

_errors = {
    401: {"description": "Sin sesión o sesión inválida"},
    403: {"description": "Política no aceptada o solo el responsable (`owner_only`)"},
    404: {"description": "Paciente no encontrado"},
    409: {"description": "Ya hay un consentimiento vigente, no lo hay para revocar o el paciente está archivado"},
}


@router.get("/privacy", response_model=PolicyStatus)
def policy_status(user: RegisteredUser) -> PolicyStatus:
    """Versión vigente de la política y si la cuenta ya la aceptó."""
    return consent_service.policy_status(user)


@router.post("/privacy/accept", response_model=PolicyStatus)
def accept_policy(user: RegisteredUser) -> PolicyStatus:
    """Acepta la versión vigente de la política. Repetirlo no cambia nada."""
    return consent_service.accept_policy(user)


@router.get("/patients/{patient_id}/consents", response_model=PatientConsents, responses=_errors)
def list_consents(patient_id: str, user: CurrentUser) -> PatientConsents:
    """Estado del consentimiento de cuidado y de detección del paciente."""
    return consent_service.list_consents(patient_id, user.uid)


@router.post(
    "/patients/{patient_id}/consents",
    response_model=PatientConsent,
    status_code=status.HTTP_201_CREATED,
    responses=_errors,
)
def register_consent(patient_id: str, body: ConsentCreate, user: CurrentUser) -> PatientConsent:
    """Registra el consentimiento del paciente o de su representante. Solo el responsable."""
    return consent_service.register(patient_id, user.uid, body)


@router.post("/patients/{patient_id}/consents/{scope}/revoke", response_model=PatientConsent, responses=_errors)
def revoke_consent(patient_id: str, scope: Scope, user: CurrentUser) -> PatientConsent:
    """Revoca el consentimiento. Sin el de detección, la cámara se detiene al instante."""
    return consent_service.revoke(patient_id, user.uid, scope)
