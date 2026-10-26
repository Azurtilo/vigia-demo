"""Capabilities are server decisions, independent from marketing benefit text."""

from django.utils import timezone

from .models import Plan, Subscription
from .services import free_plan


def capabilities(user, now=None):
    now = now or timezone.now()
    sub = Subscription.objects.select_related("plan").filter(user=user).first()
    paid = bool(sub and sub.amount_clp and sub.end and sub.end > now)
    plan = sub.plan if paid else free_plan()
    premium = paid and plan.code == "pro"
    return {
        "plan": plan.code,
        "name": plan.name,
        "price_clp": plan.amount_clp,
        "max_active_patients": plan.max_active_patients,
        "expires_at": sub.end.isoformat() if paid else None,
        "cancel_at_period_end": bool(sub and sub.cancel_at_period_end),
        "version": sub.version if sub else 0,
        "features": {
            **{
                key: True
                for key in (
                    "care_manual",
                    "medication_schedule",
                    "posture_manual",
                    "care_history",
                    "mobile_reminders",
                )
            },
            "posture_detection": premium,
            "risk_alerts": premium,
        },
        "portal_path": "/planes/mi-suscripcion/",
    }


def mobile_catalog():
    """The app compares plans from the same catalog as the web; no prices in the app."""
    plans = Plan.objects.filter(
        active=True, code__in=("free", "plus", "pro")
    ).prefetch_related("benefits")
    return [
        {
            "code": plan.code,
            "name": plan.name,
            "description": plan.description,
            "price_clp": plan.amount_clp,
            "currency": plan.currency,
            "max_active_patients": plan.max_active_patients,
            "benefits": [benefit.text for benefit in plan.benefits.all()],
        }
        for plan in plans
    ]


def mobile_capabilities(user):
    """Adds fields only, so installed apps that ignore them keep working."""
    return {**capabilities(user), "plans": mobile_catalog(), "change_plan_path": "/planes/"}
