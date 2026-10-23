import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Plan(models.Model):
    code = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=180)
    amount_clp = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="CLP", editable=False)
    active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    max_active_patients = models.PositiveIntegerField(null=True, blank=True)
    catalog_before_care = models.JSONField(default=dict, editable=False, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(currency="CLP"), name="plan_currency_clp"
            ),
            models.CheckConstraint(
                condition=Q(max_active_patients__isnull=True)
                | Q(max_active_patients__gt=0),
                name="plan_patient_limit_positive",
            ),
        ]

    @property
    def price_label(self):
        return (
            "Gratis"
            if not self.amount_clp
            else f"${self.amount_clp:,}".replace(",", ".")
        )

    def __str__(self):
        return self.name


class PlanBenefit(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="benefits")
    text = models.CharField(max_length=220)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "order"], name="plan_benefit_order_unique"
            )
        ]


class Subscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    plan_name = models.CharField(max_length=60)
    amount_clp = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="CLP")
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def price_label(self):
        return (
            "Gratis"
            if not self.amount_clp
            else f"${self.amount_clp:,}".replace(",", ".")
        )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(currency="CLP"), name="subscription_currency_clp"
            ),
            models.CheckConstraint(
                condition=(
                    Q(amount_clp=0, start__isnull=True, end__isnull=True)
                    | Q(
                        amount_clp__gt=0, start__isnull=False, end__gt=models.F("start")
                    )
                ),
                name="subscription_period_valid",
            ),
        ]


class SimulatedPaymentMethod(models.Model):
    FIXTURES = [
        ("visa_ok", "Visa aprobada"),
        ("mastercard_ok", "Mastercard aprobada"),
        ("declined", "Rechazo de prueba"),
        ("insufficient", "Fondos insuficientes de prueba"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    holder = models.CharField(max_length=100)
    fixture_code = models.CharField(max_length=20, choices=FIXTURES)
    brand = models.CharField(max_length=20)
    last4 = models.CharField(max_length=4)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-default", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    month__gte=1, month__lte=12, year__gte=2000, year__lte=2099
                ),
                name="method_expiry_valid",
            ),
            models.CheckConstraint(
                condition=Q(
                    fixture_code__in=[
                        "visa_ok",
                        "mastercard_ok",
                        "declined",
                        "insufficient",
                    ]
                ),
                name="method_fixture_valid",
            ),
            models.CheckConstraint(
                condition=Q(last4__regex=r"^[0-9]{4}$"), name="method_last4_valid"
            ),
            models.UniqueConstraint(
                fields=["user", "fixture_code", "month", "year"],
                condition=Q(active=True),
                name="method_active_unique",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(default=True, active=True),
                name="method_default_unique",
            ),
        ]

    @property
    def label(self):
        return f"{self.brand} •••• {self.last4}"

    @property
    def expiry(self):
        return f"{self.month:02d}/{self.year % 100:02d}"

    def __str__(self):
        return self.label


class SimulatedOperation(models.Model):
    TYPES = [
        (value, label)
        for value, label in (
            ("purchase", "Contratación"),
            ("change", "Cambio de plan"),
            ("renew", "Renovación"),
            ("free", "Cambio a Free"),
            ("cancel", "Cancelación programada"),
            ("resume", "Cancelación retirada"),
        )
    ]
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    method = models.ForeignKey(
        SimulatedPaymentMethod, null=True, on_delete=models.SET_NULL
    )
    plan_name = models.CharField(max_length=60)
    amount_clp = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="CLP")
    method_label = models.CharField(max_length=45, blank=True)
    kind = models.CharField(max_length=10, choices=TYPES)
    approved = models.BooleanField()
    idempotency_key = models.UUIDField()
    payload = models.CharField(max_length=64)
    previous_end = models.DateTimeField(null=True)
    period_start = models.DateTimeField(null=True)
    period_end = models.DateTimeField(null=True)
    cancellation = models.BooleanField(default=False)
    error_code = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "idempotency_key"], name="operation_idempotency_unique"
            ),
            models.CheckConstraint(
                condition=Q(currency="CLP"), name="operation_currency_clp"
            ),
            models.CheckConstraint(
                condition=Q(
                    kind__in=["purchase", "change", "renew", "free", "cancel", "resume"]
                ),
                name="operation_kind_valid",
            ),
        ]

    @property
    def price_label(self):
        return f"${self.amount_clp:,}".replace(",", ".")
