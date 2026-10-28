"""Agenda del día: medicamentos y tareas, en la hora local del paciente."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import Field

from app.models.care import TaskKind, TaskLog
from app.models.medication import DoseLog
from app.models.user import ApiModel


class MedicationAgendaItem(ApiModel):
    kind: Literal["medication"] = "medication"
    medication_id: str
    name: str
    dose: str
    instructions: str | None
    scheduled_at: datetime | None  # None para "si es necesario"
    local_time: str | None  # hora configurada, p. ej. "08:00"
    status: Literal["pending", "given", "delayed", "omitted"]
    log: DoseLog | None = None


class TaskAgendaItem(ApiModel):
    kind: Literal["task"] = "task"
    task_id: str | None  # None: cambio de posición registrado sin tarea
    title: str
    description: str | None
    task_kind: TaskKind
    assigned_to: str | None
    scheduled_at: datetime | None
    local_time: str | None
    status: Literal["pending", "done", "skipped"]
    log: TaskLog | None = None


AgendaItem = Annotated[MedicationAgendaItem | TaskAgendaItem, Field(discriminator="kind")]


class AgendaFeatures(ApiModel):
    """Funciones del plan del RESPONSABLE del paciente (la app muestra u oculta acciones con esto)."""

    extended_care_tracking: bool
    position_changes: bool


class Agenda(ApiModel):
    patient_id: str
    date: date
    time_zone: str
    features: AgendaFeatures
    items: list[AgendaItem]
