"""Transiciones del prototipo: propiedad, precios e idempotencia en servidor."""

import hashlib
import json
import uuid
from calendar import monthrange
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Plan, SimulatedOperation, SimulatedPaymentMethod, Subscription
from .permissions import verified
from .simulator import ERRORS, expired

SALT = "PlanesApp.checkout.v1"


def free_plan():
    return Plan.objects.get(code="free", amount_clp=0, active=True)


def ensure_subscription(user):
    plan = free_plan()
    return Subscription.objects.get_or_create(
        user=user,
        defaults={
            "plan": plan,
            "plan_name": plan.name,
            "amount_clp": 0,
        },
    )[0]


def month_after(now):
    zone = ZoneInfo("America/Santiago")
    local = now.astimezone(zone)
    year, month = local.year + (local.month == 12), local.month % 12 + 1
    target = local.replace(
        year=year, month=month, day=min(local.day, monthrange(year, month)[1]), fold=0
    )
    # Round-trip detects nonexistent wall times; first valid minute wins.
    for _ in range(180):
        returned = target.astimezone(ZoneInfo("UTC")).astimezone(zone)
        if returned.replace(tzinfo=None) == target.replace(tzinfo=None):
            return target.astimezone(ZoneInfo("UTC"))
        target += timedelta(minutes=1)
    raise ValidationError("No se pudo calcular el próximo período.")


def summary(user, now=None):
    now = now or timezone.now()
    sub = Subscription.objects.select_related("plan").filter(user=user).first()
    plan = sub.plan if sub else free_plan()
    state = "Activa"
    if sub and sub.end and sub.end <= now:
        if sub.cancel_at_period_end:
            plan, state = free_plan(), "Cancelada; plan Free activo"
        else:
            state = "Vencida"
    elif sub and sub.cancel_at_period_end:
        state = "Cancelación programada"
    return {
        "subscription": sub,
        "plan": plan,
        "state": state,
        "version": sub.version if sub else 0,
        "is_paid": bool(sub and sub.amount_clp and plan.code != "free"),
        "can_renew": bool(
            sub
            and sub.amount_clp
            and sub.end <= now
            and not sub.cancel_at_period_end
            and sub.plan.active
        ),
        "can_resume": bool(
            sub and sub.end and sub.end > now and sub.cancel_at_period_end
        ),
    }


def proposal(user, plan, kind, method=None):
    from CuidadosApp.capacity import fingerprint

    sub = Subscription.objects.filter(user=user).first()
    return signing.dumps(
        {
            "user": user.pk,
            "plan": plan.pk,
            "amount": plan.amount_clp,
            "version": sub.version if sub else 0,
            "kind": kind,
            "method": method.pk if method else None,
            "nonce": str(uuid.uuid4()),
            "patients": [list(row) for row in fingerprint(user)],
        },
        salt=SALT,
    )


def read_proposal(token, user):
    try:
        data = signing.loads(token, salt=SALT, max_age=900)
        uuid.UUID(data["nonce"])
        if data["user"] != user.pk:
            raise signing.BadSignature
        return data
    except (signing.BadSignature, KeyError, ValueError, TypeError):
        raise ValidationError(
            "La revisión expiró o no es válida. Recarga la página antes de confirmar."
        ) from None


def locked_user(user):
    actor = get_user_model().objects.select_for_update().get(pk=user.pk)
    if not actor.is_active:
        raise PermissionDenied
    return actor


@transaction.atomic
def execute(
    user,
    token,
    expected_kind,
    expected_plan=None,
    method_id=None,
    selected_patients=None,
):
    from CuidadosApp.capacity import apply_commercial, validate_selection

    actor = locked_user(user)
    data = read_proposal(token, actor)
    if data["kind"] != expected_kind or (
        expected_plan and data["plan"] != expected_plan.pk
    ):
        raise ValidationError("La operación no corresponde a esta revisión.")
    # Payment choice is a signed offer plus the submitted own choice, checked on POST.
    data["selected_method"] = int(method_id) if method_id else None
    try:
        data["selected_patients"] = sorted(int(pk) for pk in (selected_patients or []))
    except (TypeError, ValueError):
        raise ValidationError("La selección de pacientes no es válida.") from None
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    previous = SimulatedOperation.objects.filter(
        user=actor, idempotency_key=data["nonce"]
    ).first()
    if previous:
        if previous.payload != digest:
            raise ValidationError(
                "Esta confirmación ya se usó con otros datos. Revisa nuevamente."
            )
        return previous
    sub = ensure_subscription(actor)
    sub = Subscription.objects.select_for_update().get(pk=sub.pk)
    if sub.version != data["version"]:
        raise ValidationError("Tu suscripción cambió. Recarga y revisa la operación.")
    plan = Plan.objects.get(pk=data["plan"])
    if expected_kind not in ("cancel", "resume") and (
        not plan.active or plan.amount_clp != data["amount"]
    ):
        raise ValidationError("El plan o su precio cambió. Revisa la oferta actual.")
    now = timezone.now()
    state = summary(actor, now)
    limit = (
        free_plan().max_active_patients
        if expected_kind == "cancel"
        else plan.max_active_patients
        if expected_kind in ("purchase", "renew")
        else None
    )
    selected = validate_selection(
        actor, limit, data["selected_patients"], data.get("patients", [])
    )
    method, error = None, ""
    amount = 0
    start, end = sub.start, sub.end
    kind = expected_kind
    if kind in ("purchase", "renew"):
        if not verified(actor):
            raise PermissionDenied
        if kind == "renew":
            if not state["can_renew"] or plan.pk != sub.plan_id:
                raise ValidationError("Esta suscripción no admite renovación ahora.")
        elif state["plan"].pk == plan.pk and state["state"] != "Vencida":
            raise ValidationError("Ya tienes este plan. No se realizó ningún cargo.")
        amount = plan.amount_clp
        if amount:
            method = (
                SimulatedPaymentMethod.objects.select_for_update()
                .filter(
                    user=actor,
                    pk=method_id,
                    active=True,
                )
                .first()
            )
            if not method or expired(method.month, method.year, now):
                raise ValidationError("Elige un método propio vigente.")
            error = method.fixture_code if method.fixture_code in ERRORS else ""
            start, end = now, month_after(now)
            kind = (
                "renew"
                if kind == "renew"
                else ("change" if sub.amount_clp else "purchase")
            )
        else:
            kind, start, end = "free", None, None
    elif kind == "cancel":
        if not sub.amount_clp or not sub.end or sub.end <= now:
            raise ValidationError("No tienes un período pagado vigente que cancelar.")
    elif kind == "resume":
        if not state["can_resume"]:
            raise ValidationError("La cancelación ya terminó o no está programada.")
        if not any(
            not expired(card.month, card.year, now)
            for card in SimulatedPaymentMethod.objects.filter(user=actor, active=True)
        ):
            raise ValidationError(
                "Agrega un método de prueba vigente antes de retirar la cancelación."
            )
    else:
        raise ValidationError("Operación inválida.")
    operation = SimulatedOperation.objects.create(
        user=actor,
        plan=plan,
        plan_name=plan.name,
        amount_clp=amount,
        method=method,
        method_label=method.label if method else "",
        kind=kind,
        approved=not error,
        error_code=error,
        idempotency_key=data["nonce"],
        payload=digest,
        previous_end=sub.end,
        period_start=start if not error else sub.start,
        period_end=end if not error else sub.end,
        cancellation=(
            kind == "cancel"
            or (kind != "resume" and bool(error) and sub.cancel_at_period_end)
        ),
    )
    if error:
        return operation
    if kind in ("purchase", "change", "renew", "free"):
        sub.plan, sub.plan_name, sub.amount_clp = plan, plan.name, amount
        sub.start, sub.end = start, end
        sub.cancel_at_period_end, sub.canceled_at = False, None
    elif kind == "cancel":
        if sub.cancel_at_period_end:
            # Repeated independently reviewed cancellation preserves original date/version.
            return operation
        sub.cancel_at_period_end, sub.canceled_at = True, now
    else:
        sub.cancel_at_period_end, sub.canceled_at = False, None
    sub.version += 1
    sub.save()
    apply_commercial(actor, sub, kind, selected, now)
    return operation


@transaction.atomic
def add_method(user, cleaned):
    actor = locked_user(user)
    if not verified(actor):
        raise PermissionDenied
    fixture, brand, last4 = cleaned["fixture"]
    if SimulatedPaymentMethod.objects.filter(
        user=actor,
        fixture_code=fixture,
        month=cleaned["month"],
        year=cleaned["year"],
        active=True,
    ).exists():
        raise ValidationError("Ya tienes esta tarjeta de prueba con ese vencimiento.")
    return SimulatedPaymentMethod.objects.create(
        user=actor,
        holder=cleaned["holder"],
        fixture_code=fixture,
        brand=brand,
        last4=last4,
        month=cleaned["month"],
        year=cleaned["year"],
        default=not SimulatedPaymentMethod.objects.filter(
            user=actor, active=True
        ).exists(),
    )


@transaction.atomic
def set_default(user, method):
    actor = locked_user(user)
    if not verified(actor):
        raise PermissionDenied
    current = SimulatedPaymentMethod.objects.select_for_update().get(
        pk=method.pk, user=actor, active=True
    )
    if expired(current.month, current.year):
        raise ValidationError("Esta tarjeta de prueba está vencida.")
    SimulatedPaymentMethod.objects.filter(user=actor, default=True).update(
        default=False
    )
    current.default = True
    current.save(update_fields=["default"])


@transaction.atomic
def remove_method(user, method, cancel_token=None, selected_patients=None):
    from CuidadosApp.capacity import apply_commercial, fingerprint, validate_selection

    actor = locked_user(user)
    if not verified(actor):
        raise PermissionDenied
    current = SimulatedPaymentMethod.objects.select_for_update().get(
        pk=method.pk, user=actor, active=True
    )
    others = SimulatedPaymentMethod.objects.filter(user=actor, active=True).exclude(
        pk=current.pk
    )
    state = summary(actor)
    sub = state["subscription"]
    if not others.exists() and sub and sub.amount_clp and not sub.cancel_at_period_end:
        if sub.end > timezone.now():
            if not cancel_token:
                raise ValidationError(
                    "Confirma la cancelación al término para retirar tu última tarjeta."
                )
            execute(actor, cancel_token, "cancel", selected_patients=selected_patients)
        else:
            # An expired subscription cannot renew after the last method is removed.
            offered = read_proposal(cancel_token, actor) if cancel_token else None
            if offered and (
                offered["kind"] != "cancel" or offered["version"] != sub.version
            ):
                raise ValidationError("La revisión de cancelación cambió. Recarga.")
            if fingerprint(actor) and not offered:
                raise ValidationError(
                    "Revisa la selección de pacientes antes de retirar la última tarjeta."
                )
            selected = validate_selection(
                actor,
                free_plan().max_active_patients,
                selected_patients,
                offered.get("patients", []) if offered else [],
            )
            sub.cancel_at_period_end, sub.canceled_at = True, timezone.now()
            sub.version += 1
            sub.save()
            apply_commercial(actor, sub, "cancel", selected, timezone.now())
            SimulatedOperation.objects.create(
                user=actor,
                plan=sub.plan,
                plan_name=sub.plan_name,
                amount_clp=0,
                kind="cancel",
                approved=True,
                idempotency_key=uuid.uuid4(),
                payload="last-method",
                previous_end=sub.end,
                period_start=sub.start,
                period_end=sub.end,
                cancellation=True,
            )
    current.default, current.active = False, False
    current.save(update_fields=["default", "active"])
    if not others.filter(default=True).exists():
        replacement = others.first()
        if replacement:
            replacement.default = True
            replacement.save(update_fields=["default"])
