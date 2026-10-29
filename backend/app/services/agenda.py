"""Agenda del día del paciente: medicamentos y tareas, en su hora local.

Lo programado se calcula desde los horarios; lo registrado se lee de una consulta por colección.
Los registros que ya no calzan con un horario (porque este cambió) se muestran igual:
lo registrado nunca se oculta.
"""

from datetime import date, datetime

from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.schedule import local_day_bounds, occurrence_key, occurrences_on
from app.models.agenda import Agenda, AgendaFeatures, MedicationAgendaItem, TaskAgendaItem
from app.services import care
from app.services import medications as meds_service
from app.services import patients as patients_service
from app.services.care_common import owner_features, patient_tz


def _in_day_range(collection, start: datetime, end: datetime) -> dict[str, dict]:
    query = collection.where(filter=FieldFilter("agendaAt", ">=", start)).where(filter=FieldFilter("agendaAt", "<", end))
    return {s.id: s.to_dict() for s in query.stream()}


def _active_on(item, day: date) -> bool:
    return item.active and item.start_date <= day and (item.end_date is None or day <= item.end_date)


def agenda(patient_id: str, uid: str, day: date | None) -> Agenda:
    access = patients_service.get_access(patient_id, uid, "patient.view")
    tz = patient_tz(access)
    day = day or datetime.now(tz).date()
    start, end = local_day_bounds(day, tz)
    items: list[MedicationAgendaItem | TaskAgendaItem] = []

    # Medicamentos
    meds = {s.id: meds_service.to_medication(s.id, patient_id, s.to_dict()) for s in meds_service.meds_collection(patient_id).stream()}
    dose_logs = _in_day_range(meds_service.logs_collection(patient_id), start, end)
    for med in meds.values():
        if med.schedule_type == "fixed" and _active_on(med, day):
            for occ in occurrences_on(med.schedule, tz, day):
                log_id = f"{med.id}_{occurrence_key(occ.at)}"
                items.append(_med_item(med, occ.at, occ.local_time, log_id, dose_logs.pop(log_id, None)))
    for log_id, log in dose_logs.items():
        at = log.get("scheduledAt")
        items.append(_med_item(meds.get(log["medicationId"]), at, _hhmm(at, tz), log_id, log))

    # Tareas y cambios de posición
    tasks = {s.id: care.to_task(s.id, patient_id, s.to_dict()) for s in care.tasks_collection(patient_id).stream()}
    task_logs = _in_day_range(care.task_logs_collection(patient_id), start, end)
    for task in tasks.values():
        if task.schedule_type == "fixed" and _active_on(task, day):
            for occ in occurrences_on(task.schedule, tz, day):
                log_id = f"{task.id}_{occurrence_key(occ.at)}"
                items.append(_task_item(task, occ.at, occ.local_time, log_id, task_logs.pop(log_id, None)))
    for log_id, log in task_logs.items():
        at = log.get("scheduledAt")
        items.append(_task_item(tasks.get(log.get("taskId")), at, _hhmm(at, tz), log_id, log))

    def sort_key(item):
        if item.scheduled_at:
            return item.scheduled_at
        logged = item.log.actual_at if isinstance(item, MedicationAgendaItem) and item.log else None
        logged = logged or (item.log.done_at if isinstance(item, TaskAgendaItem) and item.log else None)
        return logged or end

    items.sort(key=sort_key)
    features = owner_features(access)
    return Agenda(
        patient_id=patient_id,
        date=day,
        time_zone=str(tz),
        features=AgendaFeatures(
            extended_care_tracking=bool(features.get("extendedCareTracking")),
            position_changes=bool(features.get("positionChanges")),
        ),
        items=items,
    )


def _hhmm(at: datetime | None, tz) -> str | None:
    return at.astimezone(tz).strftime("%H:%M") if at else None


def _med_item(med, at, local_time, log_id: str, log: dict | None) -> MedicationAgendaItem:
    return MedicationAgendaItem(
        medication_id=med.id if med else log["medicationId"],
        name=med.name if med else log["medicationName"],
        dose=log["dose"] if log else med.dose,
        instructions=med.instructions if med else None,
        scheduled_at=at,
        local_time=local_time,
        status=log["status"] if log else "pending",
        log=meds_service.to_log(log_id, log) if log else None,
    )


def _task_item(task, at, local_time, log_id: str, log: dict | None) -> TaskAgendaItem:
    return TaskAgendaItem(
        task_id=task.id if task else log.get("taskId"),
        title=task.title if task else log["title"],
        description=task.description if task else None,
        task_kind=task.kind if task else log["kind"],
        assigned_to=task.assigned_to if task else None,
        scheduled_at=at,
        local_time=local_time,
        status=log["status"] if log else "pending",
        log=care.to_task_log(log_id, log) if log else None,
    )
