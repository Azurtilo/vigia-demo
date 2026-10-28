"""Endpoints de pacientes. Toda la autorización ocurre en app.services.patients."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_user
from app.models.patient import Patient, PatientCreate, PatientUpdate
from app.models.user import UserProfile
from app.services import patients as patients_service

router = APIRouter(prefix="/patients", tags=["pacientes"])

CurrentUser = Annotated[UserProfile, Depends(get_current_user)]

_errors = {
    401: {"description": "Sin sesión o sesión inválida"},
    403: {"description": "Sin permiso, solo dueño, o límite del plan alcanzado (`plan_limit_reached`)"},
    404: {"description": "El paciente no existe o no tienes relación con él"},
}


@router.post("", response_model=Patient, status_code=status.HTTP_201_CREATED, responses=_errors)
def create_patient(body: PatientCreate, user: CurrentUser) -> Patient:
    """Registra un paciente. Quien lo crea queda como responsable (dueño). Respeta el límite del plan."""
    return patients_service.create_patient(user.uid, body)


@router.get("", response_model=list[Patient], responses=_errors)
def list_patients(
    user: CurrentUser,
    status_filter: Annotated[Literal["active", "archived", "all"], Query(alias="status")] = "active",
) -> list[Patient]:
    """Pacientes con los que tienes relación (propios o a los que te invitaron)."""
    return patients_service.list_patients(user.uid, None if status_filter == "all" else status_filter)


@router.get("/{patient_id}", response_model=Patient, responses=_errors)
def get_patient(patient_id: str, user: CurrentUser) -> Patient:
    return patients_service.get_patient(patient_id, user.uid)


@router.patch("/{patient_id}", response_model=Patient, responses={**_errors, 409: {"description": "Archivado"}})
def update_patient(patient_id: str, body: PatientUpdate, user: CurrentUser) -> Patient:
    """Modifica solo los campos enviados. Requiere el permiso `patient.edit`."""
    return patients_service.update_patient(patient_id, user.uid, body)


@router.post("/{patient_id}/archive", response_model=Patient, responses={**_errors, 409: {"description": "Ya archivado"}})
def archive_patient(patient_id: str, user: CurrentUser) -> Patient:
    """Archiva al paciente (conserva todo su historial) y libera un cupo del plan. Solo el dueño."""
    return patients_service.set_patient_status(patient_id, user.uid, "archived")


@router.post(
    "/{patient_id}/reactivate", response_model=Patient, responses={**_errors, 409: {"description": "Ya activo"}}
)
def reactivate_patient(patient_id: str, user: CurrentUser) -> Patient:
    """Reactiva un paciente archivado si el plan lo permite. Solo el dueño."""
    return patients_service.set_patient_status(patient_id, user.uid, "active")
