"""Explicit, ordered erasure (spec 014). PROTECT still blocks accidental deletes."""

import uuid

from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from CuidadosApp.models import (
    AccessCodeAttempt,
    CapacitySelection,
    CareEvent,
    CareTask,
    DetectionNode,
    Medication,
    MobileDevice,
    Patient,
    PatientAccess,
    PatientInvitation,
    PostureObservation,
    PostureTimer,
    ReminderReceipt,
)
from CuidadosApp.services import acting
from PlanesApp.services import locked_user

from .models import AccountConsent, PatientConsent, PrivacyOperation
from .names import ERASED_PREFIX


def erase_patient_rows(patient):
    """Delete a patient and everything that references it; caller holds the lock."""
    counts = {
        "observations": PostureObservation.objects.filter(
            Q(node__patient=patient) | Q(phone_patient=patient)
        ).delete()[0]
    }
    DetectionNode.objects.filter(patient=patient).delete()
    PostureTimer.objects.filter(patient=patient).delete()  # it points to an event
    events = CareEvent.objects.filter(patient=patient)
    counts["records"] = events.count()
    while events.exists():
        # Corrections reference their original (PROTECT): delete leaves first.
        referenced = CareEvent.objects.filter(
            corrected_event__isnull=False
        ).values("corrected_event")
        events.exclude(pk__in=referenced).delete()
    ReminderReceipt.objects.filter(patient=patient).delete()
    Medication.objects.filter(patient=patient).delete()
    CareTask.objects.filter(patient=patient).delete()
    PatientAccess.objects.filter(patient=patient).delete()
    PatientInvitation.objects.filter(patient=patient).delete()
    PatientConsent.objects.filter(patient=patient).delete()
    patient.delete()
    return counts


@transaction.atomic
def delete_patient(user, pk, typed_name):
    _, _, patient, _ = acting(user, pk, "erase_patient")
    if (typed_name or "").strip().casefold() != patient.name.strip().casefold():
        raise ValidationError("El nombre no coincide. No se eliminó nada.")
    counts = erase_patient_rows(patient)
    PrivacyOperation.objects.create(kind="delete_patient", counts=counts)


def end_sessions(user):
    """Web sessions and app session tokens are both Django sessions."""
    for session in Session.objects.filter(expire_date__gt=timezone.now()):
        if session.get_decoded().get("_auth_user_id") == str(user.pk):
            session.delete()


@transaction.atomic
def erase_account(user, password="", confirmation=""):
    from allauth.mfa.models import Authenticator
    from allauth.socialaccount.models import SocialAccount
    from allauth.account.models import EmailAddress
    from PlanesApp.models import SimulatedPaymentMethod

    actor = locked_user(user)
    if actor.has_usable_password():
        if not actor.check_password(password or ""):
            raise ValidationError("La contraseña no es correcta. No se eliminó nada.")
    elif (confirmation or "").strip() != actor.username:
        # Accounts created only with Google confirm by typing their username.
        raise ValidationError("Escribe tu nombre de usuario para confirmar.")
    patients = list(Patient.objects.filter(owner=actor))
    for patient in patients:  # D-065: the titular's patients go with the account
        erase_patient_rows(patient)
    PatientAccess.objects.filter(user=actor, revoked_at__isnull=True).update(
        revoked_at=timezone.now(), revoked_by=actor
    )
    MobileDevice.objects.filter(user=actor).delete()
    for model in (
        EmailAddress,
        SocialAccount,
        Authenticator,
        SimulatedPaymentMethod,
        CapacitySelection,
        ReminderReceipt,
        AccessCodeAttempt,
        AccountConsent,
    ):
        model.objects.filter(user=actor).delete()
    profile = getattr(actor, "profile", None)
    if profile and profile.image and profile.image.name != "profile.webp":
        profile.image.delete(save=False)
        profile.image = "profile.webp"
        profile.save(update_fields=["image"])
    end_sessions(actor)
    # The row stays only so records on other titulars' patients keep an author.
    actor.username = f"{ERASED_PREFIX}{uuid.uuid4().hex[:16]}"
    actor.email = actor.first_name = actor.last_name = ""
    actor.is_active = actor.is_staff = actor.is_superuser = False
    actor.set_unusable_password()
    actor.save()
    PrivacyOperation.objects.create(
        kind="delete_account", counts={"patients": len(patients)}
    )
