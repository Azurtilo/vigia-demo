"""Esquemas de pacientes. Minimización de datos: solo lo necesario para organizar el cuidado.

No se usan escalas clínicas: movilidad y necesidades son texto libre que escribe el responsable.
"""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import ConfigDict, Field, StringConstraints, field_validator
from pydantic.alias_generators import to_camel

from app.core.permissions import Permission, Relation
from app.core.schedule import DEFAULT_TIME_ZONE, validate_time_zone
from app.models.user import ApiModel

PatientStatus = Literal["active", "archived"]

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class EmergencyContact(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=6, max_length=20, pattern=r"^\+?[0-9 ]+$")
    relation: str | None = Field(default=None, max_length=40)


class _PatientFields(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    birth_date: date | None = None
    mobility: str | None = Field(default=None, max_length=500)
    care_needs: str | None = Field(default=None, max_length=1000)
    allergies: list[ShortText] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=2000)
    emergency_contacts: list[EmergencyContact] = Field(default_factory=list, max_length=3)

    @field_validator("birth_date")
    @classmethod
    def _plausible_birth_date(cls, value: date | None) -> date | None:
        if value is not None and not (date(1900, 1, 1) <= value <= date.today()):
            raise ValueError("La fecha de nacimiento no es válida.")
        return value


class PatientCreate(_PatientFields):
    display_name: str = Field(min_length=1, max_length=80)
    # Los horarios de medicamentos y tareas se interpretan en esta zona (no en la del teléfono).
    time_zone: str = DEFAULT_TIME_ZONE

    _valid_tz = field_validator("time_zone")(validate_time_zone)


class PatientUpdate(_PatientFields):
    """PATCH: solo se modifican los campos enviados. Enviar null borra un campo opcional."""

    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    time_zone: str | None = None
    allergies: list[ShortText] | None = Field(default=None, max_length=20)
    emergency_contacts: list[EmergencyContact] | None = Field(default=None, max_length=3)

    @field_validator("display_name", "time_zone")
    @classmethod
    def _not_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Este campo no puede quedar vacío.")
        return value

    @field_validator("time_zone")
    @classmethod
    def _valid_tz(cls, value: str) -> str:
        return validate_time_zone(value)


class Patient(_PatientFields):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    owner_uid: str
    display_name: str
    time_zone: str
    status: PatientStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Relación y permisos de quien consulta (la app los usa para mostrar u ocultar acciones).
    my_relation: Relation
    my_permissions: list[Permission]


class PlanUsage(ApiModel):
    plan_id: str
    plan_name: str
    max_patients: int | None
    active_patients: int
    can_add_patient: bool
