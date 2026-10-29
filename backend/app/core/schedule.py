"""Horarios en hora local del paciente y su conversión a instantes UTC.

Los horarios se guardan en hora local ("08:00") y las tomas/tareas se calculan al consultar.
Cambios de hora (Chile y otras zonas):
- Hora inexistente (adelanto de reloj): se corre por el tamaño del salto (00:30 → 01:30).
- Hora repetida (atraso de reloj): se usa la primera ocurrencia.
Si dos horas configuradas caen en el mismo instante tras el ajuste, se cuentan una sola vez.
"""

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ConfigDict, Field, StringConstraints, field_validator
from pydantic.alias_generators import to_camel

from app.models.user import ApiModel

DEFAULT_TIME_ZONE = "America/Santiago"
_TZ_FORMAT = re.compile(r"^[A-Za-z_]+(/[A-Za-z0-9_+\-]+)*$")

LocalTime = Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]


def validate_time_zone(value: str) -> str:
    if not _TZ_FORMAT.match(value):
        raise ValueError("Zona horaria no válida.")
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("Zona horaria no válida.") from None
    return value


class Schedule(ApiModel):
    """Horas locales fijas y, opcionalmente, días de la semana (1 = lunes … 7 = domingo; vacío = todos)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    times: list[LocalTime] = Field(min_length=1, max_length=12)
    days_of_week: list[Annotated[int, Field(ge=1, le=7)]] = Field(default_factory=list, max_length=7)

    @field_validator("times", "days_of_week")
    @classmethod
    def _unique_sorted(cls, value: list) -> list:
        return sorted(set(value))


@dataclass(frozen=True)
class Occurrence:
    local_date: date
    local_time: str  # hora configurada ("00:30"), aunque el cambio de hora la haya corrido
    at: datetime  # instante real en UTC


def local_to_utc(day: date, hhmm: str, tz: ZoneInfo) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    # fold=0 aplica las reglas descritas arriba para horas inexistentes y repetidas.
    return datetime.combine(day, time(hour, minute), tzinfo=tz).astimezone(UTC)


def local_day_bounds(day: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """[inicio, fin) del día local en UTC. Un día local puede durar 23, 24 o 25 horas."""
    return local_to_utc(day, "00:00", tz), local_to_utc(day + timedelta(days=1), "00:00", tz)


def occurrences_on(schedule: Schedule, tz: ZoneInfo, day: date) -> list[Occurrence]:
    if schedule.days_of_week and day.isoweekday() not in schedule.days_of_week:
        return []
    seen: dict[datetime, Occurrence] = {}
    for hhmm in schedule.times:
        at = local_to_utc(day, hhmm, tz)
        seen.setdefault(at, Occurrence(day, hhmm, at))
    return sorted(seen.values(), key=lambda o: o.at)


def local_date_of(instant: datetime, tz: ZoneInfo) -> date:
    return instant.astimezone(tz).date()


def occurrence_key(at: datetime) -> str:
    """Parte del ID determinista de un registro: 20260115T1100Z."""
    return at.astimezone(UTC).strftime("%Y%m%dT%H%MZ")
