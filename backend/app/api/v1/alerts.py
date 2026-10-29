"""Endpoints de alertas y de dispositivos para push. La autorización ocurre en app.services."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.alerts import Alert, AlertPage, DeviceRegistration, ReminderMode
from app.models.user import UserProfile
from app.services import alerts as alerts_service
from app.services import devices as devices_service

router = APIRouter(tags=["alertas"])

CurrentUser = Annotated[UserProfile, Depends(get_current_user)]

_errors = {
    401: {"description": "Sin sesión o sesión inválida"},
    403: {"description": "Sin el permiso `alerts.handle`"},
    404: {"description": "Paciente o alerta no encontrados"},
}


@router.get("/me/alerts", response_model=AlertPage, responses=_errors)
def my_alerts(user: CurrentUser) -> AlertPage:
    """Últimas 50 alertas de los pacientes en que tienes `alerts.handle`, de la más reciente a la más antigua."""
    return alerts_service.my_alerts(user.uid)


@router.get("/patients/{patient_id}/alerts", response_model=AlertPage, responses=_errors)
def list_alerts(patient_id: str, user: CurrentUser, cursor: str | None = None) -> AlertPage:
    """Alertas del paciente de a 30. Para la página siguiente, envía `cursor = nextCursor`."""
    return alerts_service.list_alerts(patient_id, user.uid, cursor)


@router.post(
    "/patients/{patient_id}/alerts/{alert_id}/attend",
    response_model=Alert,
    responses={**_errors, 409: {"description": "La alerta ya fue atendida"}},
)
def attend(patient_id: str, alert_id: str, user: CurrentUser) -> Alert:
    """Marca la alerta como atendida, con quién y cuándo."""
    return alerts_service.attend(patient_id, alert_id, user.uid)


@router.post("/devices", responses={400: {"description": "La instalación pertenece a otra cuenta"}})
def register_device(body: DeviceRegistration, user: CurrentUser) -> dict:
    """Activa o desactiva los avisos push de esta instalación."""
    return devices_service.register(user.uid, body)


@router.post("/devices/reminder-mode")
def reminder_mode(body: ReminderMode, user: CurrentUser) -> dict:
    """Indica si los recordatorios de cambio de posición se programan en el teléfono."""
    return devices_service.reminder_mode(user.uid, body)
