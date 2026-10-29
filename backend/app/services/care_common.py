"""Utilidades compartidas por medicamentos, tareas y agenda."""

from datetime import timedelta
from zoneinfo import ZoneInfo

from fastapi import status

from app.core.errors import AppError
from app.core.schedule import DEFAULT_TIME_ZONE, Schedule
from app.services import plans
from app.services.patients import Access

CLOCK_SKEW = timedelta(minutes=2)  # tolerancia para relojes de teléfonos levemente adelantados


def unprocessable(code: str, message: str) -> AppError:
    return AppError(status.HTTP_422_UNPROCESSABLE_CONTENT, code, message)


def require_active_patient(access: Access) -> None:
    if access.patient["status"] != "active":
        raise AppError(status.HTTP_409_CONFLICT, "patient_archived", "Un paciente archivado es de solo lectura.")


def patient_tz(access: Access) -> ZoneInfo:
    return ZoneInfo(access.patient.get("timeZone", DEFAULT_TIME_ZONE))


def schedule_from(data: dict | None) -> Schedule | None:
    return Schedule(times=data["times"], days_of_week=data.get("daysOfWeek", [])) if data else None


def schedule_to(schedule: Schedule | None) -> dict | None:
    return {"times": schedule.times, "daysOfWeek": schedule.days_of_week} if schedule else None


def owner_features(access: Access) -> dict:
    """Funciones del plan del DUEÑO del paciente: es su plan el que aplica a todos los miembros."""
    _, plan = plans.read_plan_for_user(access.patient["ownerUid"])
    return plan.get("features", {})


def require_feature(access: Access, feature: str, what: str) -> None:
    if not owner_features(access).get(feature):
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "plan_feature_unavailable",
            f"{what} no está incluido en el plan del responsable del paciente.",
        )
