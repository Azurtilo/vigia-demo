"""Consent and privacy operations (spec 014). No personal data in PrivacyOperation."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class AccountConsent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="privacy_consents",
    )
    policy_version = models.CharField(max_length=20)
    accepted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "policy_version"], name="account_consent_once"
            )
        ]


class PatientConsent(models.Model):
    SCOPES = [("cuidado", "Datos de cuidado"), ("deteccion", "Detección con cámara")]
    BASES = [
        ("titular", "El propio paciente"),
        ("representante", "Un representante del paciente"),
    ]

    patient = models.ForeignKey(
        "CuidadosApp.Patient", on_delete=models.PROTECT, related_name="consents"
    )
    scope = models.CharField(max_length=10, choices=SCOPES)
    basis = models.CharField(max_length=14, choices=BASES)
    representative_name = models.CharField(max_length=120, blank=True)
    representative_relation = models.CharField(max_length=60, blank=True)
    policy_version = models.CharField(max_length=20)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    recorded_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-recorded_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "scope"],
                condition=Q(revoked_at__isnull=True),
                name="patient_consent_active_once",
            ),
            models.CheckConstraint(
                condition=Q(scope__in=["cuidado", "deteccion"]),
                name="patient_consent_scope_valid",
            ),
            models.CheckConstraint(
                condition=Q(basis="titular")
                | (
                    Q(basis="representante")
                    & ~Q(representative_name="")
                    & ~Q(representative_relation="")
                ),
                name="patient_consent_representative_named",
            ),
        ]


class PrivacyOperation(models.Model):
    """Trace of exports, deletions and purges: kind, time and counts only."""

    KINDS = [
        ("export_account", "Exportación de cuenta"),
        ("export_patient", "Exportación de paciente"),
        ("delete_patient", "Eliminación de paciente"),
        ("delete_account", "Eliminación de cuenta"),
        ("purge", "Purga por plazo"),
    ]

    kind = models.CharField(max_length=16, choices=KINDS)
    created_at = models.DateTimeField(auto_now_add=True)
    counts = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at", "-pk"]
