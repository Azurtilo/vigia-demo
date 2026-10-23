"""All care mutations lock the owner first, then validate ownership and state."""

import hashlib
import json
import uuid
from datetime import date, time, timedelta

from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from PlanesApp.services import locked_user

from .capacity import archive_ids, capacity_state, materialize, require_eligible
from .models import (
    CareEvent,
    CareGuide,
    CareTask,
    Medication,
    MedicationTime,
    Patient,
    PostureTimer,
)

SALT = "CuidadosApp.action.v1"


def action_token(user, patient, kind, subject=0, version=0, **extra):
    return signing.dumps(
        {
            "user": user.pk,
            "patient": patient.pk if patient else 0,
            "kind": kind,
            "subject": subject,
            "version": version,
            "reference": str(uuid.uuid4()),
            **extra,
        },
        salt=SALT,
    )


def read_action(user, token, patient=None, kind=None):
    try:
        data = signing.loads(token, salt=SALT, max_age=172800)
        uuid.UUID(data["reference"])
        if (
            data["user"] != user.pk
            or (patient is not None and data["patient"] != patient.pk)
            or (kind and data["kind"] != kind)
        ):
            raise signing.BadSignature
        return data
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        raise ValidationError(
            "Esta acción expiró o no es válida. Recarga y revisa antes de confirmar."
        ) from None


def own_patient(user, pk):
    try:
        pk = int(pk)
    except (ValueError, TypeError):
        raise Http404 from None
    return get_object_or_404(Patient, pk=pk, owner=user)


def digest(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, default=str).encode()
    ).hexdigest()


def replay(user, reference, payload):
    previous = CareEvent.objects.filter(author=user, reference=reference).first()
    if previous and previous.snapshot.get("payload") != payload:
        raise ValidationError(
            "La confirmación ya se usó con otros datos. Revisa nuevamente."
        )
    return previous


@transaction.atomic
def save_patient(user, cleaned, pk=None, version=None):
    actor = locked_user(user)
    materialize(actor)
    if pk:
        patient = own_patient(actor, pk)
        if version is None or patient.version != version:
            raise ValidationError("La ficha cambió. Recarga antes de guardar.")
    else:
        state = capacity_state(actor)
        if state["pending"] or (
            state["limit"] is not None and state["count"] >= state["limit"]
        ):
            raise ValidationError(
                "Alcanzaste el límite de pacientes activos. Archiva uno o cambia de plan."
            )
        patient = Patient(owner=actor)
    for field in (
        "name",
        "birth_date",
        "notes",
        "contact_name",
        "contact_phone",
        "contact_relation",
    ):
        setattr(
            patient,
            field,
            cleaned.get(field) or (None if field == "birth_date" else ""),
        )
    if patient.birth_date and patient.birth_date > timezone.localdate():
        raise ValidationError("La fecha de nacimiento no puede ser futura.")
    patient.version += 1
    patient.full_clean()
    patient.save()
    return patient


@transaction.atomic
def set_patient_active(user, pk, token, active):
    actor = locked_user(user)
    patient = own_patient(actor, pk)
    data = read_action(actor, token, patient, "reactivate" if active else "archive")
    materialize(actor)
    patient.refresh_from_db()
    if patient.version != data["version"]:
        raise ValidationError("El estado del paciente cambió. Revisa nuevamente.")
    if active:
        if patient.active:
            return patient
        state = capacity_state(actor)
        if state["pending"] or (
            state["limit"] is not None and state["count"] >= state["limit"]
        ):
            raise ValidationError(
                "No hay cupo disponible para reactivar este paciente."
            )
        patient.active, patient.archived_at = True, None
        patient.version += 1
        patient.save()
        for model in (Medication, CareTask):
            model.objects.filter(patient=patient).update(
                schedule_effective_at=timezone.now(), version=F("version") + 1
            )
        # Old reminders stay paused until an explicit new care action/resume.
    else:
        archive_ids(actor, [pk], timezone.now())
    return patient


@transaction.atomic
def save_daily(user, pk, form, object_pk=None, task=False):
    actor = locked_user(user)
    patient = own_patient(actor, pk)
    require_eligible(actor, patient)
    model = CareTask if task else Medication
    if object_pk:
        obj = get_object_or_404(model, pk=object_pk, patient=patient)
        if obj.version != form.cleaned_data["version"]:
            raise ValidationError("El horario cambió. Recarga antes de guardar.")
    else:
        obj = model(patient=patient)
    for field in (
        ["name", "notes", "time", "start_date", "end_date", "active"]
        if task
        else ["name", "dose", "notes", "start_date", "end_date", "active"]
    ):
        setattr(obj, field, form.cleaned_data[field])
    obj.version += 1
    obj.schedule_effective_at = timezone.now()
    obj.full_clean()
    obj.save()
    if not task:
        obj.times.all().delete()
        MedicationTime.objects.bulk_create(
            [MedicationTime(medication=obj, time=t) for t in form.cleaned_data["hours"]]
        )
    return obj


@transaction.atomic
def record_posture(user, pk, token, guide, interval, note=""):
    actor = locked_user(user)
    patient = own_patient(actor, pk)
    data = read_action(actor, token, patient, "posture")
    payload = digest(
        {"token": data, "guide": guide.pk, "interval": interval, "note": note}
    )
    previous = replay(actor, data["reference"], payload)
    if previous:
        return previous
    require_eligible(actor, patient)
    timer, _ = PostureTimer.objects.get_or_create(patient=patient)
    if timer.generation != data["version"]:
        raise ValidationError(
            "El reloj cambió. Revisa la próxima postura antes de confirmar."
        )
    guide = get_object_or_404(CareGuide, pk=guide.pk, active=True, category="posture")
    if interval not in (60, 90, 120) or len(note) > 1000:
        raise ValidationError("Intervalo o nota inválidos.")
    now = timezone.now()
    event = CareEvent.objects.create(
        patient=patient,
        author=actor,
        reference=data["reference"],
        kind="posture",
        status="done",
        occurred_at=now,
        snapshot={
            "patient": patient.name,
            "label": guide.title,
            "guide": guide.code,
            "guide_version": guide.version,
            "interval": interval,
            "payload": payload,
        },
        note=note,
    )
    timer.last_event, timer.interval, timer.anchor_at = event, interval, now
    timer.next_due_at, timer.paused = now + timedelta(minutes=interval), False
    timer.generation += 1
    timer.save()
    return event


@transaction.atomic
def configure_timer(user, pk, token, action, interval):
    actor = locked_user(user)
    patient = own_patient(actor, pk)
    data = read_action(actor, token, patient, "timer")
    require_eligible(actor, patient)
    if action == "start":
        if interval not in (60, 90, 120):
            raise ValidationError("Intervalo inválido.")
        timer, created = PostureTimer.objects.get_or_create(patient=patient)
        if not created or data["version"] != 0:
            raise ValidationError("El reloj ya existe. Recarga para consultar su estado.")
        timer.interval = interval
        timer.anchor_at = timezone.now()
        timer.next_due_at = timer.anchor_at + timedelta(minutes=interval)
        timer.generation = 1
        timer.save()
        return
    timer = get_object_or_404(PostureTimer, patient=patient)
    if timer.generation != data["version"] or interval not in (60, 90, 120):
        raise ValidationError("El reloj cambió o el intervalo no es válido. Recarga.")
    if action == "pause":
        timer.paused, timer.next_due_at = True, None
    elif action == "resume":
        if not timer.paused:
            raise ValidationError("El reloj ya está activo.")
        timer.anchor_at, timer.paused = timezone.now(), False
        timer.interval = interval
        timer.next_due_at = timer.anchor_at + timedelta(minutes=interval)
    elif action == "interval":
        timer.interval = interval
        timer.anchor_at = (timer.last_event.occurred_at if timer.last_event else timer.anchor_at)
        if timer.anchor_at is None:
            raise ValidationError("El reloj no tiene fecha de inicio.")
        timer.next_due_at = (
            None if timer.paused else timer.anchor_at + timedelta(minutes=interval)
        )
    else:
        raise ValidationError("Acción de reloj inválida.")
    timer.generation += 1
    timer.save()


@transaction.atomic
def record_daily(user, pk, token, status, note):
    from .scheduling import occurrence, wall_instant

    actor = locked_user(user)
    patient = own_patient(actor, pk)
    data = read_action(actor, token, patient)
    if (
        data["kind"] not in ("medication", "care")
        or status not in ("done", "omitted")
        or (status == "omitted" and not note.strip())
        or len(note) > 1000
    ):
        raise ValidationError("Revisa el resultado y el motivo del cuidado.")
    payload = digest({"token": data, "status": status, "note": note})
    previous = replay(actor, data["reference"], payload)
    if previous:
        return previous
    require_eligible(actor, patient)
    obj = get_object_or_404(
        Medication if data["kind"] == "medication" else CareTask,
        pk=data["subject"],
        patient=patient,
        active=True,
    )
    if obj.version != data["version"]:
        raise ValidationError(
            "El medicamento o cuidado cambió. Revisa su horario actual."
        )
    occurrence_date = date.fromisoformat(data["date"])
    if (
        occurrence_date
        not in (timezone.localdate(), timezone.localdate() - timedelta(days=1))
        or (obj.start_date and occurrence_date < obj.start_date)
        or (obj.end_date and occurrence_date > obj.end_date)
    ):
        raise ValidationError("La fecha de esta actividad ya no es válida.")
    hour = data.get("time")
    if data["kind"] == "medication" and hour not in [
        t.time.strftime("%H:%M") for t in obj.times.all()
    ]:
        raise ValidationError("Este horario ya no existe.")
    if data["kind"] == "care" and hour != (
        obj.time.strftime("%H:%M") if obj.time else None
    ):
        raise ValidationError("Este horario de cuidado cambió.")
    item = occurrence(obj, occurrence_date, hour, data["kind"], actor)
    if CareEvent.objects.filter(patient=patient, occurrence_key=item["key"]).exists():
        raise ValidationError(
            "Esta actividad ya tiene un registro. Consulta el historial."
        )
    scheduled = (
        wall_instant(occurrence_date, time.fromisoformat(hour)) if hour else None
    )
    if scheduled and scheduled < obj.schedule_effective_at:
        raise ValidationError("Este horario es anterior a la programación actual.")
    return CareEvent.objects.create(
        patient=patient,
        author=actor,
        reference=data["reference"],
        kind=data["kind"],
        status=status,
        occurrence_key=item["key"],
        occurred_at=timezone.now(),
        note=note,
        snapshot={
            "patient": patient.name,
            "label": obj.name,
            "dose": getattr(obj, "dose", ""),
            "scheduled": scheduled.isoformat() if scheduled else "Sin horario",
            "payload": payload,
        },
    )


@transaction.atomic
def correct_event(user, pk, event_pk, token, note):
    actor = locked_user(user)
    patient = own_patient(actor, pk)
    original = get_object_or_404(CareEvent, patient=patient, pk=event_pk)
    data = read_action(actor, token, patient, "correction")
    if data["subject"] != original.pk or not 2 <= len(note.strip()) <= 1000:
        raise ValidationError("La corrección no corresponde al registro.")
    payload = digest({"token": data, "note": note})
    previous = replay(actor, data["reference"], payload)
    if previous:
        return previous
    return CareEvent.objects.create(
        patient=patient,
        author=actor,
        reference=data["reference"],
        kind="correction",
        status="corrected",
        occurred_at=timezone.now(),
        corrected_event=original,
        note=note,
        snapshot={
            "patient": patient.name,
            "label": original.snapshot.get("label", "Registro"),
            "payload": payload,
        },
    )
