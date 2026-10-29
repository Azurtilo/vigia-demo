"""Plan de cuidados: tareas, su registro y cambios de posición.

Las pautas (qué hacer y cada cuánto) las configura el responsable; la app no impone frecuencias clínicas.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.core.schedule import Schedule
from app.models.user import ApiModel

TaskKind = Literal["general", "position_change"]
TaskScheduleType = Literal["fixed", "unscheduled"]
TaskLogStatus = Literal["done", "skipped"]
# Lista descriptiva (no clínica): boca arriba, lado izquierdo, lado derecho, boca abajo, sentado, otra.
Position = Literal["supine", "left_side", "right_side", "prone", "sitting", "other"]


class _Strict(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


def _tz_aware(*values: datetime | None) -> None:
    if any(v is not None and v.tzinfo is None for v in values):
        raise ValueError("Las horas deben incluir zona horaria (por ejemplo, terminar en Z o -03:00).")


def _check_position(position: str | None, position_other: str | None) -> None:
    if position == "other" and not (position_other and position_other.strip()):
        raise ValueError("Describe la posición cuando eliges 'otra'.")
    if position != "other" and position_other is not None:
        raise ValueError("La descripción solo se usa con la posición 'otra'.")


class CareTaskCreate(_Strict):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    kind: TaskKind = "general"
    schedule_type: TaskScheduleType
    schedule: Schedule | None = None
    start_date: date
    end_date: date | None = None
    assigned_to: str | None = Field(default=None, max_length=128, description="uid de un miembro del paciente")

    @model_validator(mode="after")
    def _consistent(self) -> "CareTaskCreate":
        if self.schedule_type == "fixed" and self.schedule is None:
            raise ValueError("Una tarea con horario necesita al menos una hora.")
        if self.schedule_type == "unscheduled" and self.schedule is not None:
            raise ValueError("Una tarea sin horario no lleva horas.")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("La fecha de término no puede ser anterior a la de inicio.")
        return self


class CareTaskUpdate(_Strict):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    schedule_type: TaskScheduleType | None = None
    schedule: Schedule | None = None
    start_date: date | None = None
    end_date: date | None = None
    assigned_to: str | None = Field(default=None, max_length=128)
    active: bool | None = None


class CareTask(ApiModel):
    id: str
    patient_id: str
    title: str
    description: str | None
    kind: TaskKind
    schedule_type: TaskScheduleType
    schedule: Schedule | None
    start_date: date
    end_date: date | None
    assigned_to: str | None
    active: bool
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class _TaskLogFields(_Strict):
    status: TaskLogStatus
    done_at: datetime | None = None  # si se omite en "done", se usa la hora actual
    reason: str | None = Field(default=None, max_length=500)
    note: str | None = Field(default=None, max_length=1000)
    position: Position | None = None
    position_other: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def _consistent(self):
        _tz_aware(self.done_at)
        if self.status == "skipped":
            if not (self.reason and self.reason.strip()):
                raise ValueError("Indica el motivo cuando una tarea no se realiza.")
            if self.done_at is not None or self.position is not None:
                raise ValueError("Una tarea omitida no lleva hora de realización ni posición.")
        _check_position(self.position, self.position_other)
        return self


class TaskLogCreate(_TaskLogFields):
    # Ocurrencia de la agenda a la que corresponde. No se envía en tareas sin horario.
    scheduled_at: datetime | None = None

    @model_validator(mode="after")
    def _scheduled_tz(self) -> "TaskLogCreate":
        _tz_aware(self.scheduled_at)
        return self


class TaskLogCorrection(_TaskLogFields):
    pass


class PositionChangeCreate(_Strict):
    """Cambio de posición registrado sin una tarea programada."""

    position: Position
    position_other: str | None = Field(default=None, max_length=100)
    at: datetime | None = None  # si se omite, la hora actual
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _consistent(self) -> "PositionChangeCreate":
        _tz_aware(self.at)
        _check_position(self.position, self.position_other)
        return self


class TaskLog(ApiModel):
    id: str
    task_id: str | None  # None: cambio de posición registrado sin tarea
    title: str
    kind: TaskKind
    scheduled_at: datetime | None
    status: TaskLogStatus
    done_at: datetime | None
    reason: str | None
    note: str | None
    position: Position | None
    position_other: str | None
    recorded_by: str
    recorded_at: datetime | None = None
    corrections: int = 0
