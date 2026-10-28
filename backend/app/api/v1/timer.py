"""Endpoints del reloj de cambio de posición. La autorización ocurre en app.services."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.timer import TimerAction, TimerSchedule, TimerState
from app.models.user import UserProfile
from app.services import timer as timer_service

router = APIRouter(tags=["reloj de posición"])

CurrentUser = Annotated[UserProfile, Depends(get_current_user)]

_errors = {
    401: {"description": "Sin sesión o sesión inválida"},
    403: {"description": "Sin `care.record`, sin consentimiento de cuidado o sin cambios de posición en el plan"},
    404: {"description": "Paciente no encontrado"},
    409: {"description": "`timer_exists`, `timer_missing`, `timer_changed`, `timer_running` o paciente archivado"},
}


@router.get("/patients/{patient_id}/timer", response_model=TimerState, responses=_errors)
def get_timer(patient_id: str, user: CurrentUser) -> TimerState:
    """Estado del reloj; `exists: false` si aún no se creó."""
    return timer_service.get_timer(patient_id, user.uid)


@router.post("/patients/{patient_id}/timer", response_model=TimerState, responses=_errors)
def act(patient_id: str, body: TimerAction, user: CurrentUser) -> TimerState:
    """Crea, pausa, reanuda o cambia el intervalo (60, 90 o 120 minutos). Envía la `generation` vigente."""
    return timer_service.act(patient_id, user.uid, body)


@router.get("/me/timer-schedule", response_model=TimerSchedule)
def timer_schedule(user: CurrentUser) -> TimerSchedule:
    """Próximos vencimientos para programar avisos locales en el teléfono, sin nombres."""
    return timer_service.schedule(user.uid)
