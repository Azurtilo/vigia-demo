"""Account and patient consent rules (spec 014, D-066)."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import AccountConsent, PatientConsent

MISSING = {
    "cuidado": "Registra el consentimiento de datos de cuidado de este paciente antes de agregar registros.",
    "deteccion": "Registra el consentimiento de detección con cámara de este paciente antes de usarla.",
}


def enforced():
    return getattr(settings, "PRIVACY_ENFORCED", True)


def version():
    return settings.PRIVACY_POLICY_VERSION


def account_ok(user):
    return AccountConsent.objects.filter(user=user, policy_version=version()).exists()


def accept_account(user):
    AccountConsent.objects.get_or_create(user=user, policy_version=version())


def active(patient, scope):
    return PatientConsent.objects.filter(
        patient=patient, scope=scope, revoked_at__isnull=True
    ).exists()


def require(patient, scope):
    """Patient file stays readable; new data of this scope needs live consent."""
    if enforced() and not active(patient, scope):
        raise ValidationError(MISSING[scope])


def record(patient, scope, basis, by, name="", relation=""):
    name, relation = (name or "").strip(), (relation or "").strip()
    if scope not in MISSING or basis not in ("titular", "representante"):
        raise ValidationError("Indica el alcance y quién da el consentimiento.")
    if basis == "representante" and not (name and relation):
        raise ValidationError("Indica nombre y relación del representante.")
    if active(patient, scope):
        raise ValidationError("Este consentimiento ya está registrado.")
    return PatientConsent.objects.create(
        patient=patient,
        scope=scope,
        basis=basis,
        representative_name=name if basis == "representante" else "",
        representative_relation=relation if basis == "representante" else "",
        policy_version=version(),
        recorded_by=by,
    )


@transaction.atomic
def register(user, pk, scope, basis, name="", relation=""):
    from CuidadosApp.services import acting

    actor, _, patient, _ = acting(user, pk, "manage_access")
    return record(patient, scope, basis, actor, name, relation)


@transaction.atomic
def revoke(user, pk, scope):
    from CuidadosApp.services import acting

    acting(user, pk, "manage_access")
    PatientConsent.objects.filter(
        patient_id=pk, scope=scope, revoked_at__isnull=True
    ).update(revoked_at=timezone.now())
