"""JSON exports (spec 014): never tokens, session keys nor node credentials."""

from django.db.models import Q
from django.utils import timezone

from CuidadosApp.models import (
    CareEvent,
    DetectionNode,
    MobileDevice,
    Patient,
    PostureObservation,
    PostureTimer,
)

from . import consent
from .names import author_name


def consents_of(rows):
    return [
        {
            "scope": c.scope,
            "basis": c.basis,
            "representative_name": c.representative_name,
            "representative_relation": c.representative_relation,
            "policy_version": c.policy_version,
            "recorded_at": c.recorded_at,
            "revoked_at": c.revoked_at,
        }
        for c in rows
    ]


def account_data(user):
    from allauth.account.models import EmailAddress
    from PlanesApp.models import SimulatedOperation, SimulatedPaymentMethod, Subscription

    subscription = Subscription.objects.filter(user=user).first()
    own = list(Patient.objects.filter(owner=user).values_list("pk", flat=True))
    return {
        "generated_at": timezone.now(),
        "policy_version": consent.version(),
        "account": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined,
            "last_login": user.last_login,
        },
        "emails": list(
            EmailAddress.objects.filter(user=user).values("email", "verified", "primary")
        ),
        "policy_acceptances": list(
            user.privacy_consents.values("policy_version", "accepted_at")
        ),
        "subscription": {
            "plan": subscription.plan_name,
            "amount_clp": subscription.amount_clp,
            "start": subscription.start,
            "end": subscription.end,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }
        if subscription
        else None,
        "payment_methods": list(
            SimulatedPaymentMethod.objects.filter(user=user).values(
                "holder", "brand", "last4", "month", "year", "active", "created_at"
            )
        ),
        "simulated_operations": list(
            SimulatedOperation.objects.filter(user=user).values(
                "plan_name", "amount_clp", "currency", "kind", "approved", "created_at"
            )
        ),
        "devices": list(
            MobileDevice.objects.filter(user=user).values(
                "platform", "active", "updated_at"
            )
        ),
        "own_patient_ids": own,
        "patient_links": list(
            user.care_accesses.values("patient_id", "role", "accepted_at", "revoked_at")
        ),
        # Records on someone else's patient: what this person did, not that file.
        "authored_records": [
            {
                "occurred_at": e.occurred_at,
                "kind": e.kind,
                "status": e.status,
                "label": e.snapshot.get("label", ""),
            }
            for e in CareEvent.objects.filter(author=user).exclude(patient_id__in=own)
        ],
    }


def patient_data(patient):
    timer = PostureTimer.objects.filter(patient=patient).first()
    return {
        "generated_at": timezone.now(),
        "policy_version": consent.version(),
        "patient": {
            key: getattr(patient, key)
            for key in (
                "name",
                "birth_date",
                "notes",
                "contact_name",
                "contact_phone",
                "contact_relation",
                "active",
                "archived_at",
                "created_at",
            )
        },
        "consents": consents_of(patient.consents.all()),
        "medications": [
            {
                "name": m.name,
                "dose": m.dose,
                "notes": m.notes,
                "start_date": m.start_date,
                "end_date": m.end_date,
                "active": m.active,
                "times": [t.time.strftime("%H:%M") for t in m.times.all()],
            }
            for m in patient.medications.prefetch_related("times")
        ],
        "care_tasks": list(
            patient.tasks.values("name", "notes", "time", "start_date", "end_date", "active")
        ),
        "records": [
            {
                "occurred_at": e.occurred_at,
                "kind": e.kind,
                "status": e.status,
                "label": e.snapshot.get("label", ""),
                "dose": e.snapshot.get("dose", ""),
                "note": e.note,
                "author": author_name(e.author),
                "corrects": e.corrected_event_id,
                "id": e.pk,
            }
            for e in patient.events.select_related("author")
        ],
        "posture_clock": {
            "interval": timer.interval,
            "paused": timer.paused,
            "next_due_at": timer.next_due_at,
        }
        if timer
        else None,
        "observations": list(
            PostureObservation.objects.filter(
                Q(node__patient=patient) | Q(phone_patient=patient)
            ).values(
                "observed_at",
                "received_at",
                "posture",
                "confidence",
                "risk",
                "platform",
                "model_version",
                "rule_version",
            )
        ),
        "detection_nodes": list(
            DetectionNode.objects.filter(patient=patient).values(
                "name", "active", "created_at", "last_seen_at"
            )
        ),
    }
