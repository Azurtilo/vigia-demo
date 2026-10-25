"""Retention periods approved in D-064 (spec 014, P-014-01)."""

from datetime import timedelta

from django.db.models import Q

from CuidadosApp.models import (
    AccessCodeAttempt,
    PatientInvitation,
    PostureObservation,
    PushReceipt,
    ReminderReceipt,
)

# While a patient is active its care records are kept: they are the audit trail
# of delegated care (HU-03, HU-06). Revoked links stay with the patient.
RETENTION = {
    "access_code_attempts": timedelta(hours=24),
    "closed_invitations": timedelta(days=90),
    "reminder_receipts": timedelta(days=30),
    "push_receipts": timedelta(days=30),
    "observations_without_risk": timedelta(days=30),
    "observations_with_risk": timedelta(days=365),
    "archived_patients": timedelta(days=730),
}


def expired(now):
    """Querysets of rows past their period, keyed like RETENTION (patients apart)."""
    limit = {key: now - period for key, period in RETENTION.items()}
    closed = limit["closed_invitations"]
    return {
        "access_code_attempts": AccessCodeAttempt.objects.filter(
            created_at__lt=limit["access_code_attempts"]
        ),
        "closed_invitations": PatientInvitation.objects.filter(
            Q(used_at__lt=closed) | Q(revoked_at__lt=closed) | Q(expires_at__lt=closed)
        ).exclude(patientaccess__isnull=False),
        "reminder_receipts": ReminderReceipt.objects.filter(
            seen_at__lt=limit["reminder_receipts"]
        ),
        "push_receipts": PushReceipt.objects.filter(sent_at__lt=limit["push_receipts"]),
        "observations_without_risk": PostureObservation.objects.filter(
            risk="", observed_at__lt=limit["observations_without_risk"]
        ),
        "observations_with_risk": PostureObservation.objects.exclude(risk="").filter(
            observed_at__lt=limit["observations_with_risk"]
        ),
    }
