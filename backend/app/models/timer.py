"""Reloj de cambio de posición del paciente (HU-04, spec 011, RF-019-06)."""

from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.models.user import ApiModel

Interval = Literal[60, 90, 120]
TimerActionName = Literal["start", "pause", "resume", "interval"]


class TimerState(ApiModel):
    exists: bool
    interval_minutes: int | None = None
    anchor_at: datetime | None = Field(default=None, description="Desde cuándo corre el intervalo")
    next_due_at: datetime | None = None
    paused: bool = False
    generation: int = Field(default=0, description="Versión del reloj; se envía de vuelta en cada acción")
    last_position_at: datetime | None = None


class TimerAction(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    action: TimerActionName
    interval_minutes: Interval
    generation: int = Field(ge=0, description="La que devolvió la última consulta; 0 para crear el reloj")


class TimerScheduleItem(ApiModel):
    patient_id: str
    generation: int
    due: datetime


class TimerSchedule(ApiModel):
    items: list[TimerScheduleItem]
    server_time: datetime
