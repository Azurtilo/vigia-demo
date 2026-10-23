import uuid

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Patient(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(
        "Nombre", max_length=120, validators=[MinLengthValidator(2)]
    )
    birth_date = models.DateField("Fecha de nacimiento", blank=True, null=True)
    notes = models.TextField("Información relevante", max_length=2000, blank=True)
    contact_name = models.CharField(
        "Contacto de emergencia", max_length=120, blank=True
    )
    contact_phone = models.CharField(
        "Teléfono de emergencia", max_length=30, blank=True
    )
    contact_relation = models.CharField("Relación", max_length=60, blank=True)
    active = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "pk"]
        indexes = [models.Index(fields=["owner", "active"])]

    def __str__(self):
        # UserAdmin's protected-delete collector must not expose clinical names.
        return "Ficha de cuidado protegida"


class Medication(models.Model):
    schedule_effective_at = models.DateTimeField(default=timezone.now, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="medications"
    )
    name = models.CharField(
        "Medicamento", max_length=120, validators=[MinLengthValidator(2)]
    )
    dose = models.CharField("Dosis indicada", max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField("Notas", max_length=1000, blank=True)
    start_date = models.DateField("Desde", null=True, blank=True)
    end_date = models.DateField("Hasta", null=True, blank=True)
    active = models.BooleanField("Activo", default=True)
    version = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__isnull=True)
                | Q(start_date__isnull=True)
                | Q(end_date__gte=models.F("start_date")),
                name="medication_dates_valid",
            )
        ]


class MedicationTime(models.Model):
    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name="times"
    )
    time = models.TimeField()

    class Meta:
        ordering = ["time"]
        constraints = [
            models.UniqueConstraint(
                fields=["medication", "time"], name="medication_time_unique"
            )
        ]


class CareTask(models.Model):
    schedule_effective_at = models.DateTimeField(default=timezone.now, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="tasks")
    name = models.CharField(
        "Cuidado", max_length=120, validators=[MinLengthValidator(2)]
    )
    notes = models.TextField("Indicaciones", max_length=1000, blank=True)
    time = models.TimeField("Horario diario (opcional)", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField("Desde", null=True, blank=True)
    end_date = models.DateField("Hasta", null=True, blank=True)
    active = models.BooleanField("Activo", default=True)
    version = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__isnull=True)
                | Q(start_date__isnull=True)
                | Q(end_date__gte=models.F("start_date")),
                name="care_task_dates_valid",
            )
        ]


class CareGuide(models.Model):
    code = models.SlugField(unique=True)
    title = models.CharField(max_length=120)
    category = models.CharField(
        max_length=20, choices=[("posture", "Postura"), ("care", "Cuidado")]
    )
    instructions = models.JSONField(default=list)
    precautions = models.TextField()
    image = models.CharField(max_length=160)
    image_alt = models.CharField(max_length=220)
    source_url = models.URLField()
    source_title = models.CharField(max_length=120)
    version = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["pk"]

    @property
    def illustration(self):
        descriptions = {
            "supina": "Persona mayor acostada boca arriba en una cama, con almohada de cabeza y apoyo bajo las piernas.",
            "lateral-izquierda": "Persona mayor sobre su lado izquierdo, con almohada de cabeza, apoyo detrás del tronco y entre las rodillas.",
            "lateral-derecha": "Persona mayor sobre su lado derecho, con almohada de cabeza, apoyo detrás del tronco y entre las rodillas.",
            "comodidad": "Cuidadora conversa con una persona mayor en su cama y prepara una almohada para su comodidad.",
        }
        if (
            self.code in descriptions
            and self.image == f"CuidadosApp/guides/{self.code}.svg"
        ):
            return {
                "image": f"CuidadosApp/guides/{self.code}-v2.png",
                "alt": descriptions[self.code],
                "revision": "20261006",
            }
        return {"image": self.image, "alt": self.image_alt}

    def __str__(self):
        return self.title


class CareEvent(models.Model):
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="events"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reference = models.UUIDField(default=uuid.uuid4, editable=False)
    kind = models.CharField(
        max_length=12,
        choices=[
            ("posture", "Postura"),
            ("medication", "Medicamento"),
            ("care", "Cuidado"),
            ("correction", "Corrección"),
        ],
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ("done", "Realizado"),
            ("omitted", "Omitido"),
            ("corrected", "Corrección"),
        ],
    )
    occurred_at = models.DateTimeField()
    snapshot = models.JSONField(default=dict)
    occurrence_key = models.CharField(max_length=220, null=True, blank=True)
    corrected_event = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="corrections",
    )
    note = models.TextField(max_length=1000, blank=True)

    class Meta:
        ordering = ["-occurred_at", "-pk"]
        indexes = [models.Index(fields=["patient", "occurred_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["author", "reference"], name="care_event_idempotency"
            ),
            models.UniqueConstraint(
                fields=["patient", "occurrence_key"], name="care_occurrence_once"
            ),
            models.CheckConstraint(
                condition=Q(kind__in=["posture", "medication", "care", "correction"]),
                name="care_event_kind_valid",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["done", "omitted", "corrected"]),
                name="care_event_status_valid",
            ),
        ]

    def __str__(self):
        return "Registro de cuidado protegido"


class PostureTimer(models.Model):
    patient = models.OneToOneField(
        Patient, on_delete=models.PROTECT, related_name="timer"
    )
    last_event = models.ForeignKey(
        CareEvent, on_delete=models.PROTECT, null=True, blank=True
    )
    interval = models.PositiveSmallIntegerField(default=120)
    next_due_at = models.DateTimeField(null=True, blank=True)
    anchor_at = models.DateTimeField(null=True, blank=True)
    paused = models.BooleanField(default=False)
    generation = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(interval__in=[60, 90, 120]), name="posture_interval_valid"
            )
        ]


class ReminderReceipt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    key = models.CharField(max_length=240)
    seen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "key"], name="care_reminder_once")
        ]


class CapacitySelection(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    subscription = models.ForeignKey("PlanesApp.Subscription", on_delete=models.PROTECT)
    subscription_version = models.PositiveIntegerField()
    patients = models.JSONField(default=list)
    effective_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

# Kept separate for readability; registered under the existing CuidadosApp.
from .mobile_models import DetectionNode, MobileDevice, PostureObservation, PushReceipt  # noqa: E402,F401
