"""Per-patient roles (spec 013): the owner is the titular; others need a live link.

Every entry point resolves the patient here. No role means 404 (the patient's
existence is not revealed); a role without the action means 403.
"""

from collections import defaultdict

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404

from .capacity import capacity_state
from .models import Patient, PatientAccess

TITULAR, FAMILIAR, CUIDADOR = "titular", "familiar", "cuidador"
ALL = frozenset({TITULAR, FAMILIAR, CUIDADOR})
SUPERVISORS = frozenset({TITULAR, FAMILIAR})

ACTIONS = {
    "view": ALL,
    "record": ALL,
    "correct": ALL,  # a caregiver may only correct own records (services)
    "edit_patient": SUPERVISORS,
    "configure": SUPERVISORS,
    "history": SUPERVISORS,
    "detection": SUPERVISORS,
    "archive": frozenset({TITULAR}),
    "manage_nodes": frozenset({TITULAR}),
    "manage_access": frozenset({TITULAR}),
    "leave": frozenset({FAMILIAR, CUIDADOR}),
}

# Who receives which push (D-063: risk alerts also reach the caregiver).
RECIPIENTS = {"care": frozenset({TITULAR, CUIDADOR}), "risk": ALL}


def allowed_actions(role):
    return sorted(action for action, roles in ACTIONS.items() if role in roles)


def live_links(user):
    return PatientAccess.objects.filter(
        user=user, revoked_at__isnull=True, patient__owner__is_active=True
    )


def role_for(user, patient):
    if patient.owner_id == user.pk:
        return TITULAR
    if not patient.owner.is_active:
        return None
    return (
        PatientAccess.objects.filter(
            patient=patient, user=user, revoked_at__isnull=True
        )
        .values_list("role", flat=True)
        .first()
    )


def patient_for(user, pk, action):
    try:
        pk = int(pk)
    except (ValueError, TypeError):
        raise Http404 from None
    patient = Patient.objects.select_related("owner").filter(pk=pk).first()
    role = role_for(user, patient) if patient else None
    if role is None:
        raise Http404
    if role not in ACTIONS[action]:
        raise PermissionDenied
    return patient, role


def accessible_patients(user):
    return Patient.objects.filter(
        Q(owner=user) | Q(pk__in=live_links(user).values("patient_id"))
    )


def roles_for(user):
    """Patient id → role for every patient the user can reach."""
    roles = {pk: TITULAR for pk in Patient.objects.filter(owner=user).values_list("pk", flat=True)}
    roles.update(live_links(user).values_list("patient_id", "role"))
    return roles


def active_ids_for(user, now=None, roles=ALL):
    """Eligible patients by each titular's capacity, limited to the given roles."""
    ids = list(capacity_state(user, now)["active_ids"]) if TITULAR in roles else []
    by_owner = defaultdict(list)
    for patient_id, owner_id, role in live_links(user).values_list(
        "patient_id", "patient__owner_id", "role"
    ):
        if role in roles:
            by_owner[owner_id].append(patient_id)
    owners = get_user_model().objects.in_bulk(by_owner)
    for owner_id, patient_ids in by_owner.items():
        active = set(capacity_state(owners[owner_id], now)["active_ids"])
        ids += [pk for pk in patient_ids if pk in active]
    return ids


def risk_patient_ids(user, now=None):
    """Patients whose risk alerts reach this user: any role, titular's plan."""
    from PlanesApp.entitlements import capabilities

    ids = active_ids_for(user, now, RECIPIENTS["risk"])
    enabled, allowed = {}, []
    for patient in Patient.objects.filter(pk__in=ids).select_related("owner"):
        if patient.owner_id not in enabled:
            enabled[patient.owner_id] = capabilities(patient.owner, now)["features"][
                "risk_alerts"
            ]
        if enabled[patient.owner_id]:
            allowed.append(patient.pk)
    return allowed


def recipients(patient, kind):
    """User ids that should receive a `care` or `risk` push for this patient."""
    wanted = RECIPIENTS[kind]
    ids = [patient.owner_id] if TITULAR in wanted else []
    ids += PatientAccess.objects.filter(
        patient=patient, revoked_at__isnull=True, role__in=wanted - {TITULAR}
    ).values_list("user_id", flat=True)
    return ids
