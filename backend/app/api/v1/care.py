"""Endpoints del plan de cuidados y de la agenda. La autorización ocurre en app.services."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_user
from app.models.agenda import Agenda
from app.models.care import (
    CareTask,
    CareTaskCreate,
    CareTaskUpdate,
    PositionChangeCreate,
    TaskLog,
    TaskLogCorrection,
    TaskLogCreate,
)
from app.models.history import Category, HistoryPage
from app.models.user import UserProfile
from app.services import agenda as agenda_service
from app.services import care as care_service
from app.services import history as history_service

router = APIRouter(prefix="/patients/{patient_id}", tags=["plan de cuidados"])

CurrentUser = Annotated[UserProfile, Depends(get_current_user)]

_errors = {
    401: {"description": "Sin sesión o sesión inválida"},
    403: {"description": "Sin el permiso necesario, o función no incluida en el plan (`plan_feature_unavailable`)"},
    404: {"description": "Paciente, tarea o registro no encontrado"},
    409: {"description": "Conflicto de estado (ver `error.code`)"},
}


@router.get("/agenda", response_model=Agenda, responses=_errors)
def agenda(patient_id: str, user: CurrentUser, day: Annotated[date | None, Query(alias="date")] = None) -> Agenda:
    """Medicamentos y tareas de un día (por defecto hoy), en la hora local del paciente."""
    return agenda_service.agenda(patient_id, user.uid, day)


@router.get("/history", response_model=HistoryPage, responses=_errors)
def history(
    patient_id: str,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    category: Category | None = None,
) -> HistoryPage:
    """Historial del más reciente al más antiguo. Requiere `history.view`.

    Muestra los días que permite el plan del responsable; lo anterior se conserva pero no se muestra
    (`hiddenOlderEntries`). Para la página siguiente, envía `cursor = nextCursor`.
    """
    return history_service.history(patient_id, user.uid, limit, cursor, category)


@router.post("/tasks", response_model=CareTask, status_code=status.HTTP_201_CREATED, responses=_errors)
def create_task(patient_id: str, body: CareTaskCreate, user: CurrentUser) -> CareTask:
    """Crea una tarea del plan de cuidados. Requiere `care.manage`.

    `kind: position_change` y `assignedTo` dependen del plan del responsable del paciente.
    """
    return care_service.create_task(patient_id, user.uid, body)


@router.get("/tasks", response_model=list[CareTask], responses=_errors)
def list_tasks(
    patient_id: str, user: CurrentUser, include_inactive: Annotated[bool, Query(alias="includeInactive")] = False
) -> list[CareTask]:
    return care_service.list_tasks(patient_id, user.uid, include_inactive)


@router.get("/tasks/{task_id}", response_model=CareTask, responses=_errors)
def get_task(patient_id: str, task_id: str, user: CurrentUser) -> CareTask:
    return care_service.get_task(patient_id, user.uid, task_id)


@router.patch("/tasks/{task_id}", response_model=CareTask, responses=_errors)
def update_task(patient_id: str, task_id: str, body: CareTaskUpdate, user: CurrentUser) -> CareTask:
    """Modifica lo enviado (incluido `active: false`). Requiere `care.manage`."""
    return care_service.update_task(patient_id, user.uid, task_id, body)


@router.post(
    "/tasks/{task_id}/logs",
    response_model=TaskLog,
    status_code=status.HTTP_201_CREATED,
    responses={**_errors, 409: {"description": "`task_already_recorded`: ese horario ya se registró"}},
)
def log_task(patient_id: str, task_id: str, body: TaskLogCreate, user: CurrentUser) -> TaskLog:
    """Registra una tarea como realizada (o no realizada, con motivo, según plan). Requiere `care.record`."""
    return care_service.log_task(patient_id, user.uid, task_id, body)


@router.patch("/task-logs/{log_id}", response_model=TaskLog, responses=_errors)
def correct_task_log(patient_id: str, log_id: str, body: TaskLogCorrection, user: CurrentUser) -> TaskLog:
    """Corrige un registro; el valor anterior queda guardado. Quien lo registró o el responsable."""
    return care_service.correct_task_log(patient_id, user.uid, log_id, body)


@router.post("/position-changes", response_model=TaskLog, status_code=status.HTTP_201_CREATED, responses=_errors)
def record_position_change(patient_id: str, body: PositionChangeCreate, user: CurrentUser) -> TaskLog:
    """Registra un cambio de posición sin tarea programada. Requiere `care.record` y que el plan lo incluya."""
    return care_service.record_position_change(patient_id, user.uid, body)
