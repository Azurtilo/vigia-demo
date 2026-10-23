"""Additive native-device and local detector records; never store camera frames."""

import uuid

from django.conf import settings
from django.db import models


class DetectionNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        "CuidadosApp.Patient", on_delete=models.PROTECT, related_name="detection_nodes"
    )
    name = models.CharField(max_length=80)
    credential_hash = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PostureObservation(models.Model):
    node = models.ForeignKey(DetectionNode, on_delete=models.PROTECT, null=True, blank=True)
    phone_patient = models.ForeignKey("CuidadosApp.Patient", on_delete=models.PROTECT, null=True, blank=True)
    platform = models.CharField(max_length=10, blank=True, default="")
    event_id = models.UUIDField()
    observed_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
    posture = models.CharField(
        max_length=24,
        choices=[
            (p, p)
            for p in ("supina", "lateral-izquierda", "lateral-derecha", "indeterminada")
        ],
    )
    confidence = models.FloatField()
    model_version = models.CharField(max_length=80)
    rule_version = models.CharField(max_length=80)
    risk = models.CharField(
        max_length=24,
        default="",
        blank=True,
        choices=[("", ""), ("immobility", "Inmovilidad")],
    )
    payload_hash = models.CharField(max_length=64)

    class Meta:
        ordering = ["-observed_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["node", "event_id"], name="mobile_observation_once"
            ),
            models.CheckConstraint(
                condition=models.Q(confidence__gte=0, confidence__lte=1),
                name="mobile_confidence_range",
            ),
            models.UniqueConstraint(fields=["phone_patient", "event_id"], name="phone_observation_once"),
            models.CheckConstraint(
                condition=(models.Q(node__isnull=False, phone_patient__isnull=True, platform="") |
                           models.Q(node__isnull=True, phone_patient__isnull=False, platform__in=["android", "ios"], risk="")),
                name="observation_one_origin",
            ),
        ]


class MobileDevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    installation_id = models.UUIDField(unique=True)
    token = models.CharField(max_length=4096)
    platform = models.CharField(
        max_length=10, choices=[("ios", "iOS"), ("android", "Android")]
    )
    local_posture_reminders = models.BooleanField(default=False)
    session_key = models.CharField(max_length=40)
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)


class PushReceipt(models.Model):
    device = models.ForeignKey(MobileDevice, on_delete=models.CASCADE)
    key = models.CharField(max_length=240)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["device", "key"], name="mobile_push_once")
        ]
