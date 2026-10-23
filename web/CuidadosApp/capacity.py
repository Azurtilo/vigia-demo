"""Patient eligibility shared by care actions and commercial transitions."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from PlanesApp.models import Subscription
from PlanesApp.services import free_plan, locked_user

from .models import CapacitySelection, Patient, PostureTimer


def fingerprint(user):
    return list(
        Patient.objects.filter(owner=user, active=True)
        .order_by("pk")
        .values_list("pk", "version")
    )


def capacity_state(user, now=None):
    now = now or timezone.now()
    sub = Subscription.objects.select_related("plan").filter(user=user).first()
    paid = bool(sub and sub.amount_clp and sub.end and sub.end > now)
    limit = sub.plan.max_active_patients if paid else free_plan().max_active_patients
    patients = list(Patient.objects.filter(owner=user, active=True).order_by("pk"))
    ids = [p.pk for p in patients]
    selection = CapacitySelection.objects.filter(user=user).first()
    valid = bool(
        selection
        and sub
        and selection.subscription_version == sub.version
        and selection.subscription_id == sub.pk
    )
    effective = valid and selection.effective_at <= now
    pending = False
    if effective:
        selected = set(selection.patients)
        ids = [pk for pk in ids if pk in selected]
        if limit is not None and len(ids) > limit:
            ids, pending = [], True
    elif limit is not None and len(ids) > limit:
        ids, pending = [], True
    return {
        "limit": limit,
        "active_ids": ids,
        "pending": pending,
        "selection": selection if valid else None,
        "effective_selection": bool(effective),
        "count": len(ids),
        "paid": paid,
    }


def validate_selection(user, limit, selected, offered=None):
    current = fingerprint(user)
    if offered is not None and [list(row) for row in current] != offered:
        raise ValidationError(
            "Tus pacientes cambiaron. Recarga y revisa quiénes seguirán activos."
        )
    try:
        ids = [int(pk) for pk in (selected or [])]
    except (TypeError, ValueError):
        raise ValidationError("La selección de pacientes no es válida.") from None
    own = {row[0] for row in current}
    if len(ids) != len(set(ids)) or not set(ids).issubset(own):
        raise ValidationError("Selecciona solamente tus pacientes activos.")
    if limit is not None and len(own) > limit and len(ids) != limit:
        raise ValidationError(
            f"Elige los {limit} pacientes que seguirán activos. Los demás se archivarán."
        )
    return ids if limit is not None and len(own) > limit else sorted(own)


def archive_ids(user, ids, now):
    patients = Patient.objects.filter(owner=user, active=True, pk__in=ids)
    from django.db.models import F

    patients.update(
        active=False, archived_at=now, version=F("version") + 1, updated_at=now
    )
    PostureTimer.objects.filter(patient__owner=user, patient_id__in=ids).update(
        paused=True, next_due_at=None, generation=F("generation") + 1
    )


def materialize(user, now=None):
    """Called only in an authorized atomic POST after locking the account."""
    now = now or timezone.now()
    state = capacity_state(user, now)
    if state["effective_selection"] and not state["pending"]:
        excluded = (
            Patient.objects.filter(owner=user, active=True)
            .exclude(pk__in=state["active_ids"])
            .values_list("pk", flat=True)
        )
        archive_ids(user, list(excluded), now)
        CapacitySelection.objects.filter(user=user).delete()
    return state


def apply_commercial(user, sub, kind, selected, now):
    if kind == "resume":
        CapacitySelection.objects.filter(user=user).delete()
    elif kind == "cancel":
        CapacitySelection.objects.update_or_create(
            user=user,
            defaults={
                "subscription": sub,
                "subscription_version": sub.version,
                "patients": selected,
                "effective_at": sub.end,
            },
        )
    else:
        # A successful purchase/renewal replaces the future selection.
        CapacitySelection.objects.filter(user=user).delete()
        own = Patient.objects.filter(owner=user, active=True).values_list(
            "pk", flat=True
        )
        archive_ids(user, [pk for pk in own if pk not in selected], now)


@transaction.atomic
def choose_capacity(user, selected, offered, version, future=False):
    actor = locked_user(user)
    sub = Subscription.objects.select_for_update().filter(user=actor).first()
    if (sub.version if sub else 0) != version:
        raise ValidationError("Tu suscripción cambió. Revisa nuevamente la selección.")
    state = capacity_state(actor)
    if future:
        if (
            not sub
            or not sub.cancel_at_period_end
            or not sub.end
            or sub.end <= timezone.now()
        ):
            raise ValidationError("No hay una cancelación futura que modificar.")
        ids = validate_selection(
            actor, free_plan().max_active_patients, selected, offered
        )
        apply_commercial(actor, sub, "cancel", ids, timezone.now())
    else:
        if not state["pending"]:
            raise ValidationError(
                "La capacidad ya está resuelta. Vuelve a tus cuidados."
            )
        ids = validate_selection(actor, state["limit"], selected, offered)
        archive_ids(
            actor,
            [row[0] for row in fingerprint(actor) if row[0] not in ids],
            timezone.now(),
        )
        CapacitySelection.objects.filter(user=actor).delete()


def require_eligible(user, patient, now=None):
    materialize(user, now)
    if patient.pk not in capacity_state(user, now)["active_ids"]:
        raise ValidationError(
            "Este paciente está archivado o debes elegir tus pacientes activos antes de registrar cuidados."
        )
