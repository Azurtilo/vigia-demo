"""Endpoints de cuenta: registro y perfil propio."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import Identity, get_current_user, get_identity, get_registered_user
from app.models.patient import PlanUsage
from app.models.user import RegisterRequest, UserProfile
from app.services import patients as patients_service
from app.services import users as users_service

router = APIRouter(tags=["cuenta"])

_auth_errors = {
    401: {"description": "Sin sesión o sesión inválida/expirada"},
    403: {"description": "Cuenta deshabilitada, suspendida o sin registrar"},
}


@router.post(
    "/auth/register",
    response_model=UserProfile,
    status_code=status.HTTP_201_CREATED,
    responses={**_auth_errors, 409: {"description": "La cuenta ya estaba registrada"}},
)
def register(
    body: RegisterRequest,
    identity: Annotated[Identity, Depends(get_identity)],
) -> UserProfile:
    """Crea el perfil VIGIA de quien ya creó su cuenta en Firebase Authentication.

    El rol asignado es siempre `client`. Enviar `role` u otros campos no previstos se rechaza.
    """
    return users_service.register(identity.uid, identity.email, body.display_name)


@router.get("/me", response_model=UserProfile, responses=_auth_errors)
def me(user: Annotated[UserProfile, Depends(get_registered_user)]) -> UserProfile:
    """Perfil de la persona que hace la solicitud. No exige la política: la app ve aquí si falta aceptarla."""
    return user


@router.get("/me/plan", response_model=PlanUsage, responses=_auth_errors)
def my_plan(user: Annotated[UserProfile, Depends(get_current_user)]) -> PlanUsage:
    """Plan actual y uso: cuántos pacientes activos tienes y si puedes agregar otro."""
    return patients_service.plan_usage(user.uid)
