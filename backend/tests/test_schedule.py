"""Horarios y cambios de hora. Pruebas unitarias: no necesitan emuladores."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from app.core.schedule import Schedule, local_day_bounds, occurrence_key, occurrences_on, validate_time_zone

SCL = ZoneInfo("America/Santiago")


def _utc(*args):
    return datetime(*args, tzinfo=UTC)


def test_same_local_time_in_summer_and_winter():
    schedule = Schedule(times=["08:00"])

    summer = occurrences_on(schedule, SCL, date(2026, 1, 15))
    winter = occurrences_on(schedule, SCL, date(2026, 7, 15))

    assert summer[0].at == _utc(2026, 1, 15, 11, 0)  # UTC-3
    assert winter[0].at == _utc(2026, 7, 15, 12, 0)  # UTC-4


def test_nonexistent_time_on_dst_start_is_shifted_forward():
    """6-sep-2026: el reloj salta de 00:00 a 01:00; las 00:30 no existen."""
    occ = occurrences_on(Schedule(times=["00:30"]), SCL, date(2026, 9, 6))

    assert len(occ) == 1
    assert occ[0].local_time == "00:30"
    assert occ[0].at.astimezone(SCL).strftime("%H:%M") == "01:30"


def test_times_colliding_after_dst_shift_count_once():
    occ = occurrences_on(Schedule(times=["00:30", "01:30"]), SCL, date(2026, 9, 6))

    assert len(occ) == 1


def test_repeated_time_on_dst_end_happens_once():
    """4-abr-2026: a las 24:00 el reloj vuelve a 23:00; las 23:30 ocurren dos veces."""
    occ = occurrences_on(Schedule(times=["23:30"]), SCL, date(2026, 4, 4))

    assert len(occ) == 1
    assert occ[0].at == _utc(2026, 4, 5, 2, 30)  # primera ocurrencia (UTC-3)


def test_day_lengths_around_dst():
    def hours(day):
        start, end = local_day_bounds(day, SCL)
        return (end - start).total_seconds() / 3600

    assert hours(date(2026, 9, 6)) == 23
    assert hours(date(2026, 4, 4)) == 25
    assert hours(date(2026, 7, 15)) == 24


def test_days_of_week_filter():
    schedule = Schedule(times=["09:00"], days_of_week=[1, 3, 5])  # lunes, miércoles, viernes

    assert occurrences_on(schedule, SCL, date(2026, 10, 26))  # lunes
    assert occurrences_on(schedule, SCL, date(2026, 10, 27)) == []  # martes


def test_schedule_normalizes_and_validates():
    assert Schedule(times=["20:00", "08:00", "08:00"]).times == ["08:00", "20:00"]
    for bad in (["8:00"], ["24:00"], ["12:60"], []):
        with pytest.raises(ValidationError):
            Schedule(times=bad)
    with pytest.raises(ValidationError):
        Schedule(times=["08:00"], days_of_week=[0])


def test_occurrence_key_is_utc_and_stable():
    assert occurrence_key(datetime(2026, 1, 15, 8, 0, tzinfo=SCL)) == "20260115T1100Z"


@pytest.mark.parametrize("tz", ["America/Santiago", "America/Punta_Arenas", "Pacific/Easter", "UTC"])
def test_valid_time_zones(tz):
    assert validate_time_zone(tz) == tz


@pytest.mark.parametrize("tz", ["Marte/Olympus", "../etc/passwd", "", "America/Santiago "])
def test_invalid_time_zones(tz):
    with pytest.raises(ValueError):
        validate_time_zone(tz)
