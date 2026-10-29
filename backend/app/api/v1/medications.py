"""Endpoints de medicamentos y tomas. Toda la autorización ocurre en app.services.medications."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_user
from app.models.medication import (
    DoseLog,
    DoseLogCorrection,
    DoseLogCreate,
    Medication,
    MedicationCreate,
    MedicationUpdate,
)
from app.models.user import UserProfile
from app.services import medications as meds_service

router = APIRouter(prefix="/patients/{patient_id}", tags=["medicamentos"])

CurrentUser = Annotated[UserProfile, Depends(get_current_user)]

_errors = {
    401: {"description": "Sin sesión o sesión inválida"},
    403: {"description": "Sin el permiso necesario"},
    404: {"description": "Paciente, medicamento o registro no encontrado"},
    409: {"description": "Conflicto de estado (ver `error.code`)"},
}


@router.post("/medications", response_model=Medication, status_code=status.HTTP_201_CREATED, responses=_errors)
def create_medication(patient_id: str, body: MedicationCreate, user: CurrentUser) -> Medication:
    """Registra un medicamento tal como fue indicado. Requiere `meds.manage`.

    `scheduleType`: `fixed` (con `schedule`: horas locales del paciente y días opcionales) o `as_needed`.
    """
    return meds_service.create_medication(patient_id, user.uid, body)


@router.get("/medications", response_model=list[Medication], responses=_errors)
def list_medications(
    patient_id: str, user: CurrentUser, include_inactive: Annotated[bool, Query(alias="includeInactive")] = False
) -> list[Medication]:
    return meds_service.list_medications(patient_id, user.uid, include_inactive)


@router.get("/medications/{medication_id}", response_model=Medication, responses=_errors)
def get_medication(patient_id: str, medication_id: str, user: CurrentUser) -> Medication:
    return meds_service.get_medication(patient_id, user.uid, medication_id)


@router.patch("/medications/{medication_id}", response_model=Medication, responses=_errors)
def update_medication(patient_id: str, medication_id: str, body: MedicationUpdate, user: CurrentUser) -> Medication:
    """Modifica lo enviado (incluido `active: false` para desactivar). Guarda la versión anterior. Requiere `meds.manage`."""
    return meds_service.update_medication(patient_id, user.uid, medication_id, body)


@router.post(
    "/medications/{medication_id}/doses",
    response_model=DoseLog,
    status_code=status.HTTP_201_CREATED,
    responses={**_errors, 409: {"description": "`dose_already_recorded`: esa toma ya se registró"}},
)
def log_dose(patient_id: str, medication_id: str, body: DoseLogCreate, user: CurrentUser) -> DoseLog:
    """Registra una toma como dada, retrasada (con motivo) u omitida (con motivo). Requiere `meds.administer`.

    En horario fijo, `scheduledAt` debe ser exactamente el de una toma de la agenda.
    """
    return meds_service.log_dose(patient_id, user.uid, medication_id, body)


@router.patch("/doses/{log_id}", response_model=DoseLog, responses=_errors)
def correct_dose(patient_id: str, log_id: str, body: DoseLogCorrection, user: CurrentUser) -> DoseLog:
    """Corrige un registro de toma; el valor anterior queda guardado. Quien la registró o el responsable."""
    return meds_service.correct_dose(patient_id, user.uid, log_id, body)

