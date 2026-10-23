"""Agregados de solo lectura para el dashboard interno autorizado por Home."""

from zoneinfo import ZoneInfo

from django.db.models import Case, CharField, Count, F, Q, Sum, Value, When
from django.utils import timezone

from .models import Plan, SimulatedOperation, Subscription


def subscription_dashboard(now=None):
    now = now or timezone.now()
    month_start = now.astimezone(ZoneInfo("America/Santiago")).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    subscriptions = Subscription.objects.filter(user__is_active=True)
    paid = Q(amount_clp__gt=0)
    counts = subscriptions.aggregate(
        registered=Count("pk"),
        paid_current=Count("pk", filter=paid & Q(end__gt=now)),
        expired=Count("pk", filter=paid & Q(end__lte=now, cancel_at_period_end=False)),
        cancellation_pending=Count(
            "pk", filter=paid & Q(end__gt=now, cancel_at_period_end=True)
        ),
    )
    # La cancelación terminada equivale a Free sin modificar la fila histórica.
    grouped = (
        subscriptions.annotate(
            effective_code=Case(
                When(
                    end__lte=now,
                    cancel_at_period_end=True,
                    then=Value("free"),
                ),
                default=F("plan__code"),
                output_field=CharField(),
            )
        )
        .values("effective_code")
        .annotate(total=Count("pk"))
    )
    quantities = {row["effective_code"]: row["total"] for row in grouped}
    distribution = []
    for plan in Plan.objects.all():
        total = quantities.pop(plan.code, 0)
        if not plan.active and not total:
            continue
        distribution.append(
            {
                "code": plan.code,
                "name": plan.name,
                "total": total,
                "share": round(total * 100 / counts["registered"], 1)
                if counts["registered"]
                else 0,
                "price_label": plan.price_label,
                "is_paid": bool(plan.amount_clp),
                "active": plan.active,
            }
        )
    # Permite leer incluso un catálogo incompleto, sin seed/backfill durante GET.
    for code, total in quantities.items():
        distribution.append(
            {
                "code": code,
                "name": "Vigía Free" if code == "free" else code,
                "total": total,
                "share": round(total * 100 / counts["registered"], 1),
                "price_label": "Gratis" if code == "free" else "No disponible",
                "is_paid": code != "free",
                "active": False,
            }
        )
    monetary = SimulatedOperation.objects.filter(
        approved=True,
        kind__in=("purchase", "change", "renew"),
        created_at__gte=month_start,
        created_at__lte=now,
    ).aggregate(amount=Sum("amount_clp"), count=Count("pk"))
    volume = monetary["amount"] or 0
    return {
        **counts,
        "distribution": distribution,
        "volume_label": f"${volume:,}".replace(",", "."),
        "volume_clp": volume,
        "monetary_count": monetary["count"],
        "month_start": month_start,
        "updated_at": now,
    }
