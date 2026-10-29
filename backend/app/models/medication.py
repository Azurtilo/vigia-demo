"""Medicamentos y registros de administración.

VIGIA registra lo indicado por el responsable del tratamiento: la dosis es texto libre tal como
fue indicada; la app no calcula, sugiere ni corrige dosis u horarios.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.core.schedule import Schedule
from app.models.user import ApiModel

ScheduleType = Literal["fixed", "as_needed"]
DoseStatus = Literal["given", "delayed", "omitted"]


class _Strict(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


def _check_schedule(schedule_type: str | None, schedule: Schedule | None) -> None:
    if schedule_type == "fixed" and schedule is None:
        raise ValueError("Un medicamento con horario fijo necesita al menos una hora.")
    if schedule_type == "as_needed" and schedule is not None:
        raise ValueError("Un medicamento 'si es necesario' no lleva horario.")


class MedicationCreate(_Strict):
    name: str = Field(min_length=1, max_length=120)
    dose: str = Field(min_length=1, max_length=200, description="Tal como fue indicada, p. ej. '1 comprimido de 500 mg'")
    instructions: str | None = Field(default=None, max_length=1000)
    schedule_type: ScheduleType
    schedule: Schedule | None = None
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def _consistent(self) -> "MedicationCreate":
        _check_schedule(self.schedule_type, self.schedule)
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("La fecha de término no puede ser anterior a la de inicio.")
        return self


class MedicationUpdate(_Strict):
    """PATCH: solo cambia lo enviado. Los cambios de horario aplican a tomas futuras; lo registrado se conserva."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    dose: str | None = Field(default=None, min_length=1, max_length=200)
    instructions: str | None = Field(default=None, max_length=1000)
    schedule_type: ScheduleType | None = None
    schedule: Schedule | None = None
    start_date: date | None = None
    end_date: date | None = None
    active: bool | None = None


class Medication(ApiModel):
    id: str
    patient_id: str
    name: str
    dose: str
    instructions: str | None
    schedule_type: ScheduleType
    schedule: Schedule | None
    start_date: date
    end_date: date | None
    active: bool
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DoseLogCreate(_Strict):
    status: DoseStatus
    # Toma programada a la que corresponde (instante exacto de la agenda). No se envía en "si es necesario".
    scheduled_at: datetime | None = None
    # Hora real de administración. Si se omite en "given", se usa la hora actual.
    actual_at: datetime | None = None
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _consistent(self) -> "DoseLogCreate":
        if self.scheduled_at is not None and self.scheduled_at.tzinfo is None:
            raise ValueError("Las horas deben incluir zona horaria (por ejemplo, terminar en Z o -03:00).")
        _check_dose_fields(self.status, self.actual_at, self.reason)
        return self


class DoseLogCorrection(_Strict):
    status: DoseStatus
    actual_at: datetime | None = None
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _consistent(self) -> "DoseLogCorrection":
        _check_dose_fields(self.status, self.actual_at, self.reason)
        return self


def _check_dose_fields(status: str, actual_at: datetime | None, reason: str | None) -> None:
    if actual_at is not None and actual_at.tzinfo is None:
        raise ValueError("Las horas deben incluir zona horaria (por ejemplo, terminar en Z o -03:00).")
    if status in ("delayed", "omitted") and not (reason and reason.strip()):
        raise ValueError("Indica el motivo cuando la toma se retrasa o se omite.")
    if status == "omitted" and actual_at is not None:
        raise ValueError("Una toma omitida no lleva hora de administración.")
    if status == "delayed" and actual_at is None:
        raise ValueError("Indica a qué hora se administró la toma retrasada.")


class DoseLog(ApiModel):
    id: str
    medication_id: str
    medication_name: str
    dose: str
    scheduled_at: datetime | None
    status: DoseStatus
    actual_at: datetime | None
    reason: str | None
    recorded_by: str
    recorded_at: datetime | None = None
    corrections: int = 0
