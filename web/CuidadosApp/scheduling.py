"""Read-only agenda and reminder candidates; actions never arise from GET."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from PlanesApp.services import locked_user

from .capacity import capacity_state, materialize
from .models import (
    CareEvent,
    CareTask,
    Medication,
    PostureTimer,
    ReminderReceipt,
)
from .services import action_token

ZONE = ZoneInfo("America/Santiago")
UTC = ZoneInfo("UTC")
REMINDER_SALT = "CuidadosApp.reminder.v1"


def wall_instant(date, time):
    local = datetime.combine(date, time).replace(tzinfo=ZONE, fold=0)
    for _ in range(181):
        returned = local.astimezone(UTC).astimezone(ZONE)
        if returned.replace(tzinfo=None) == local.replace(tzinfo=None):
            return local.astimezone(UTC)
        local += timedelta(minutes=1)
    raise ValidationError("No se pudo interpretar el horario local.")


def occurrence(obj, date, hour, kind, user):
    # Version is signed in the action token. Logical slot stays stable to prevent
    # a second dose when a medication's text/version is edited the same day.
    key = f"{kind}:{obj.pk}:{date.isoformat()}:{hour or 'manual'}"
    due = wall_instant(date, time.fromisoformat(hour)) if hour else None
    return {
        "key": key,
        "kind": kind,
        "object": obj,
        "patient": obj.patient,
        "label": obj.name,
        "dose": getattr(obj, "dose", ""),
        "due": due,
        "date": date,
        "token": action_token(
            user,
            obj.patient,
            kind,
            obj.pk,
            obj.version,
            date=date.isoformat(),
            time=hour,
        ),
        "dst_adjusted": bool(due and due.astimezone(ZONE).strftime("%H:%M") != hour),
    }


def agenda(user, now=None, patient_id=None):
    now = now or timezone.now()
    ids = capacity_state(user, now)["active_ids"]
    if patient_id:
        ids = [pk for pk in ids if pk == patient_id]
    today = now.astimezone(ZONE).date()
    items = []
    for kind, objects in (
        (
            "medication",
            Medication.objects.filter(patient_id__in=ids, active=True)
            .select_related("patient")
            .prefetch_related("times"),
        ),
        (
            "care",
            CareTask.objects.filter(patient_id__in=ids, active=True).select_related(
                "patient"
            ),
        ),
    ):
        for obj in objects:
            for date in (today - timedelta(days=1), today):
                if (
                    date < obj.created_at.astimezone(ZONE).date()
                    or (obj.start_date and date < obj.start_date)
                    or (obj.end_date and date > obj.end_date)
                ):
                    continue
                hours = (
                    [t.time.strftime("%H:%M") for t in obj.times.all()]
                    if kind == "medication"
                    else [obj.time.strftime("%H:%M") if obj.time else None]
                )
                for hour in hours:
                    item = occurrence(obj, date, hour, kind, user)
                    if date < today and (not item["due"] or item["due"] > now):
                        continue
                    items.append(item)
    events = {
        e.occurrence_key: e
        for e in CareEvent.objects.filter(
            patient__owner=user, occurrence_key__in=[i["key"] for i in items]
        )
    }
    for item in items:
        item["event"] = events.get(item["key"])
        if item["event"]:
            item["label"] = item["event"].snapshot.get("label", item["label"])
            item["dose"] = item["event"].snapshot.get("dose", item["dose"])
        item["overdue"] = bool(not item["event"] and item["due"] and item["due"] <= now)
    items = [
        i
        for i in items
        if (i["date"] == today or not i["event"])
        and (
            i["event"] or not i["due"] or i["due"] >= i["object"].schedule_effective_at
        )
    ]
    return sorted(
        items,
        key=lambda i: (
            bool(i["event"]),
            i["due"] or now + timedelta(days=1),
            i["patient"].name,
        ),
    )


def reminders(user, now=None):
    now = now or timezone.now()
    ids = capacity_state(user, now)["active_ids"]
    candidates = []
    for timer in PostureTimer.objects.filter(
        patient_id__in=ids, paused=False, next_due_at__isnull=False
    ).select_related("patient"):
        left = (timer.next_due_at - now).total_seconds()
        if left <= 600:
            phase = "due" if left <= 0 else "soon"
            candidates.append(
                {
                    "key": f"posture:{timer.pk}:{timer.generation}:{phase}",
                    "patient": timer.patient,
                    "label": "Cambio de postura pendiente"
                    if phase == "due"
                    else "Cambio de postura en menos de 10 minutos",
                    "due": timer.next_due_at,
                }
            )
    for item in agenda(user, now):
        if item["overdue"]:
            candidates.append(
                {
                    "key": item["key"],
                    "patient": item["patient"],
                    "label": item["label"],
                    "due": item["due"],
                }
            )
    seen = set(
        ReminderReceipt.objects.filter(
            user=user, key__in=[i["key"] for i in candidates]
        ).values_list("key", flat=True)
    )
    return [
        {
            "key": item["key"],
            "patient_id": item["patient"].pk,
            "patient_name": item["patient"].name,
            "label": item["label"],
            "due": item["due"].isoformat(),
            "seen": item["key"] in seen,
            "token": signing.dumps(
                {"user": user.pk, "patient": item["patient"].pk, "key": item["key"]},
                salt=REMINDER_SALT,
            ),
        }
        for item in candidates
    ]


@transaction.atomic
def claim_reminder(user, token):
    actor = locked_user(user)
    materialize(actor)
    try:
        data = signing.loads(token, salt=REMINDER_SALT, max_age=120)
        if data["user"] != actor.pk:
            raise signing.BadSignature
    except (signing.BadSignature, KeyError, TypeError):
        raise ValidationError("El aviso ya no es válido.") from None
    valid = next(
        (
            r
            for r in reminders(actor)
            if r["key"] == data["key"] and r["patient_id"] == data["patient"]
        ),
        None,
    )
    if not valid:
        raise ValidationError("El cuidado o el reloj ya cambió. Actualiza la agenda.")
    _, created = ReminderReceipt.objects.get_or_create(
        user=actor, key=data["key"], defaults={"patient_id": data["patient"]}
    )
    return created
