"""Access codes for delegated care (spec 013).

A code is shown once, valid for 48 h and single use; only its SHA-256 is
stored. Failed attempts are counted in the database so every process shares
the limit, and they are written outside the atomic block that rejects them.
"""

import hashlib
import secrets
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from PlanesApp.permissions import verified
from PlanesApp.services import locked_user

from . import access
from .models import AccessCodeAttempt, PatientAccess, PatientInvitation
from .services import acting

ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I/L
CODE_LENGTH = 10
VALID_FOR = timedelta(hours=48)
MAX_PENDING = 5
MAX_FAILURES = 5
FAILURE_WINDOW = timedelta(minutes=15)
INVALID = "El código no es válido o ya no está vigente."


def normalize(code):
    return "".join(ch for ch in str(code or "").upper() if ch.isalnum())


def code_hash(code):
    return hashlib.sha256(normalize(code).encode()).hexdigest()


def pending(patient):
    return patient.invitations.filter(
        used_at__isnull=True, revoked_at__isnull=True, expires_at__gt=timezone.now()
    )


@transaction.atomic
def create_invitation(user, pk, role):
    actor, _, patient, _ = acting(user, pk, "manage_access")
    if role not in (access.FAMILIAR, access.CUIDADOR):
        raise ValidationError("Elige si la persona será familiar o cuidador.")
    if pending(patient).count() >= MAX_PENDING:
        raise ValidationError(
            f"Ya hay {MAX_PENDING} códigos sin usar. Revoca alguno antes de crear otro."
        )
    code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
    invitation = PatientInvitation.objects.create(
        patient=patient,
        role=role,
        code_hash=code_hash(code),
        created_by=actor,
        expires_at=timezone.now() + VALID_FOR,
    )
    return invitation, f"{code[:5]}-{code[5:]}"


def check_attempts(user):
    since = timezone.now() - FAILURE_WINDOW
    if AccessCodeAttempt.objects.filter(user=user, created_at__gte=since).count() >= MAX_FAILURES:
        raise ValidationError(
            "Hiciste demasiados intentos. Espera 15 minutos y vuelve a intentarlo."
        )


def find(code, lock=False):
    rows = PatientInvitation.objects.select_related("patient__owner")
    if lock:
        rows = rows.select_for_update()
    return rows.filter(
        code_hash=code_hash(code),
        used_at__isnull=True,
        revoked_at__isnull=True,
        expires_at__gt=timezone.now(),
        patient__owner__is_active=True,
    ).first()


def checked(user, code):
    """Valid invitation for this user, or ValidationError (failures counted)."""
    if not verified(user):
        raise ValidationError("Verifica tu correo antes de unirte a un cuidado.")
    check_attempts(user)
    invitation = find(code) if len(normalize(code)) == CODE_LENGTH else None
    if invitation is None:
        AccessCodeAttempt.objects.create(user=user)
        raise ValidationError(INVALID)
    if invitation.patient.owner_id == user.pk:
        raise ValidationError("Este código es para invitar a otra persona a tu paciente.")
    if PatientAccess.objects.filter(
        patient=invitation.patient, user=user, revoked_at__isnull=True
    ).exists():
        raise ValidationError("Ya tienes acceso a este paciente.")
    return invitation


def preview(user, code):
    invitation = checked(user, code)
    return {"patient_name": invitation.patient.name, "role": invitation.role}


def accept(user, code):
    checked(user, code)
    with transaction.atomic():
        invitation = find(code)
        if invitation is None:
            raise ValidationError(INVALID)
        locked_user(invitation.patient.owner)
        invitation = find(code, lock=True)
        # Recheck under the titular's lock: a parallel use or a new link may win.
        if invitation is None or PatientAccess.objects.filter(
            patient=invitation.patient, user=user, revoked_at__isnull=True
        ).exists():
            raise ValidationError(INVALID)
        now = timezone.now()
        invitation.used_at, invitation.used_by = now, user
        invitation.save(update_fields=["used_at", "used_by"])
        return PatientAccess.objects.create(
            patient=invitation.patient,
            user=user,
            role=invitation.role,
            invitation=invitation,
            accepted_at=now,
        )


@transaction.atomic
def revoke_access(user, access_id):
    link = get_object_or_404(PatientAccess, pk=access_id, revoked_at__isnull=True)
    actor, _, _, _ = acting(user, link.patient_id, "manage_access")
    PatientAccess.objects.filter(pk=link.pk, revoked_at__isnull=True).update(
        revoked_at=timezone.now(), revoked_by=actor
    )


@transaction.atomic
def revoke_invitation(user, invitation_id):
    invitation = get_object_or_404(
        PatientInvitation, pk=invitation_id, used_at__isnull=True, revoked_at__isnull=True
    )
    acting(user, invitation.patient_id, "manage_access")
    PatientInvitation.objects.filter(pk=invitation.pk, used_at__isnull=True).update(
        revoked_at=timezone.now()
    )


@transaction.atomic
def leave(user, pk):
    actor, _, patient, _ = acting(user, pk, "leave")
    PatientAccess.objects.filter(
        patient=patient, user=actor, revoked_at__isnull=True
    ).update(revoked_at=timezone.now(), revoked_by=actor)
