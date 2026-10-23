"""Capabilities are server decisions, independent from marketing benefit text."""

from django.utils import timezone

from .models import Subscription
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
