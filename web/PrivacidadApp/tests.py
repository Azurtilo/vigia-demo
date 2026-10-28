"""Spec 014: policy, patient consent, export, erasure and purge (rules enforced)."""

import hashlib
import json
from datetime import timedelta
from io import StringIO

from allauth.account.models import EmailAddress
from django.apps import apps
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from CuidadosApp import access, invitations, services
from CuidadosApp.models import (
    AccessCodeAttempt,
    CareEvent,
    CareGuide,
    DetectionNode,
    MobileDevice,
    Patient,
    PatientAccess,
    PostureObservation,
)
from PlanesApp.models import Plan, Subscription

from . import consent, erase
from .models import AccountConsent, PatientConsent, PrivacyOperation

PASSWORD = "Demo-strong-123!"
NODE_TOKEN = "nodo-privacidad-" + "z" * 30


@override_settings(PRIVACY_ENFORCED=True)
class PrivacyBase(TestCase):
    def setUp(self):
        cache.clear()
        self.titular = self.person("titular")
        self.cuidador = self.person("cuidador")
        self.patient = Patient.objects.create(owner=self.titular, name="Rosa Demo")
        consent.record(self.patient, "cuidado", "titular", self.titular)
        self.link = PatientAccess.objects.create(
            patient=self.patient, user=self.cuidador, role="cuidador"
        )
        self.guide = CareGuide.objects.filter(category="posture", active=True).first()

    def person(self, name, accepted=True):
        user = User.objects.create_user(
            name, f"{name}@example.test", PASSWORD, first_name=name.capitalize()
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        if accepted:
            consent.accept_account(user)
        return user

    def web(self, user):
        client = Client()
        client.force_login(user)
        return client

    def api_token(self, user):
        response = Client().post(
            "/_allauth/app/v1/auth/login",
            data=json.dumps({"username": user.username, "password": PASSWORD}),
            content_type="application/json",
        )
        return response.json()["meta"]["session_token"]

    def posture(self, user, version=0):
        token = services.action_token(user, self.patient, "posture", version=version)
        return services.record_posture(user, self.patient.pk, token, self.guide, 120)

    def premium(self, user):
        plan = Plan.objects.get(code="pro")
        Subscription.objects.update_or_create(
            user=user,
            defaults={
                "plan": plan,
                "plan_name": plan.name,
                "amount_clp": plan.amount_clp,
                "start": timezone.now() - timedelta(days=1),
                "end": timezone.now() + timedelta(days=29),
            },
        )


class PolicyReadingTests(PrivacyBase):
    """Spec 018, RF-018-05..07: sections, index and exits by session."""

    SECTIONS = ("datos", "usos", "video", "acceso", "conservacion", "derechos", "cambios")

    def test_index_links_every_section(self):
        page = Client().get(reverse("PrivacidadApp:policy"))
        for section in self.SECTIONS:
            with self.subTest(section=section):
                self.assertContains(page, f'href="#{section}"', count=1)
                self.assertContains(page, f'<section id="{section}">', count=1)
        self.assertContains(page, 'class="privacy-draft"')

    def test_exits_depend_on_the_session(self):
        anonymous = Client().get(reverse("PrivacidadApp:policy"))
        self.assertContains(anonymous, f'href="{reverse("account_signup")}"')
        self.assertContains(anonymous, f'href="{reverse("account_login")}"')
        self.assertNotContains(anonymous, "Volver a mi panel")
        signed_in = self.web(self.person("lectora")).get(reverse("PrivacidadApp:policy"))
        self.assertContains(signed_in, f'href="{reverse("CuidadosApp:panel")}">Volver a mi panel')
        self.assertNotContains(signed_in, f'href="{reverse("account_signup")}"')

    def test_signup_still_opens_the_policy_in_another_tab(self):
        page = Client().get(reverse("account_signup"))
        self.assertContains(page, f'href="{reverse("PrivacidadApp:policy")}" target="_blank" rel="noopener"')


class PolicyGateTests(PrivacyBase):
    def test_policy_is_public_and_versioned(self):
        page = Client().get(reverse("PrivacidadApp:policy"))
        self.assertContains(page, consent.version())
        self.assertContains(page, "pendiente de revisión legal")

    def test_signup_requires_acceptance_and_records_it(self):
        data = {
            "username": "nueva",
            "email": "nueva@example.test",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        Client().post(reverse("account_signup"), data)
        self.assertFalse(User.objects.filter(username="nueva").exists())
        Client().post(reverse("account_signup"), {**data, "accept_privacy": "on"})
        user = User.objects.get(username="nueva")
        self.assertTrue(consent.account_ok(user))

    def test_gate_redirects_web_and_blocks_api_until_accepted(self):
        pending = self.person("pendiente", accepted=False)
        client = self.web(pending)
        response = client.get(reverse("CuidadosApp:panel"))
        self.assertRedirects(
            response,
            reverse("PrivacidadApp:accept") + "?next=/cuidados/",
            fetch_redirect_response=False,
        )
        self.assertEqual(client.get(reverse("PrivacidadApp:policy")).status_code, 200)
        api = Client().get(
            "/api/v1/patients", HTTP_X_SESSION_TOKEN=self.api_token(pending)
        )
        self.assertEqual(api.status_code, 403)
        self.assertTrue(api.json()["consent_required"])
        done = client.post(
            reverse("PrivacidadApp:accept"), {"accept": "on", "next": "/cuidados/"}
        )
        self.assertRedirects(done, "/cuidados/", fetch_redirect_response=False)
        self.assertEqual(client.get(reverse("CuidadosApp:panel")).status_code, 200)
        self.assertEqual(client.post(reverse("account_logout")).status_code, 302)

    def test_new_policy_version_asks_again(self):
        client = self.web(self.titular)
        self.assertEqual(client.get(reverse("CuidadosApp:panel")).status_code, 200)
        with self.settings(PRIVACY_POLICY_VERSION="2099-01-01"):
            response = client.get(reverse("CuidadosApp:panel"))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("PrivacidadApp:accept"), response["Location"])

    def test_open_redirect_is_ignored(self):
        pending = self.person("pendiente2", accepted=False)
        done = self.web(pending).post(
            reverse("PrivacidadApp:accept"),
            {"accept": "on", "next": "https://evil.example/"},
        )
        self.assertEqual(done["Location"], "/")


class PatientConsentTests(PrivacyBase):
    def test_patient_creation_records_who_consents(self):
        client = self.web(self.cuidador)
        url = reverse("CuidadosApp:patient_new")
        client.post(url, {"name": "Sin consentimiento"})
        missing = client.post(
            url,
            {"name": "Sin nombre", "consent_basis": "representante", "consent_confirm": "on"},
        )
        # The error sits next to each empty field, not only at the top of the form.
        self.assertContains(missing, 'id="error_1_id_representative_name"')
        self.assertContains(missing, "Indica la relación con el paciente.")
        self.assertFalse(Patient.objects.filter(owner=self.cuidador).exists())
        client.post(
            url,
            {
                "name": "Con representante",
                "consent_basis": "representante",
                "representative_name": "Hija Demo",
                "representative_relation": "Hija",
                "consent_confirm": "on",
            },
        )
        created = PatientConsent.objects.get(patient__owner=self.cuidador)
        self.assertEqual(
            (created.scope, created.basis, created.representative_name),
            ("cuidado", "representante", "Hija Demo"),
        )
        self.assertEqual(created.policy_version, consent.version())

    def test_api_creation_requires_consent_fields(self):
        headers = {"HTTP_X_SESSION_TOKEN": self.api_token(self.cuidador)}
        post = lambda data: Client().post(  # noqa: E731
            "/api/v1/patients", data=json.dumps(data), content_type="application/json", **headers
        )
        self.assertEqual(post({"name": "Sin consentimiento"}).status_code, 400)
        response = post({"name": "Con consentimiento", "consent_basis": "titular", "consent_confirm": True})
        self.assertEqual(response.status_code, 201)

    def test_existing_patient_without_consent_is_readable_but_blocked(self):
        PatientConsent.objects.filter(patient=self.patient).update(revoked_at=timezone.now())
        page = self.web(self.titular).get(reverse("CuidadosApp:patient", args=[self.patient.pk]))
        self.assertContains(page, "no se aceptan registros nuevos")
        with self.assertRaisesMessage(ValidationError, "consentimiento"):
            self.posture(self.titular)
        self.assertFalse(CareEvent.objects.exists())

    def test_revoke_and_register_from_patient_page(self):
        client = self.web(self.titular)
        client.post(reverse("PrivacidadApp:consent_revoke", args=[self.patient.pk, "cuidado"]))
        self.assertFalse(consent.active(self.patient, "cuidado"))
        client.post(
            reverse("PrivacidadApp:consent", args=[self.patient.pk]),
            {"scope": "cuidado", "consent_basis": "titular", "consent_confirm": "on"},
        )
        self.assertTrue(consent.active(self.patient, "cuidado"))
        # Only the titular manages consent.
        response = self.web(self.cuidador).post(
            reverse("PrivacidadApp:consent_revoke", args=[self.patient.pk, "cuidado"])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(consent.active(self.patient, "cuidado"))

    def test_detection_needs_its_own_consent(self):
        self.premium(self.titular)
        DetectionNode.objects.create(
            patient=self.patient,
            name="Cámara",
            credential_hash=hashlib.sha256(NODE_TOKEN.encode()).hexdigest(),
        )
        status = lambda: Client().get(  # noqa: E731
            "/api/v1/edge/status", HTTP_AUTHORIZATION="Bearer " + NODE_TOKEN
        ).status_code
        self.assertEqual(status(), 403)  # fail-closed: the node stops capturing
        consent.record(self.patient, "deteccion", "titular", self.titular)
        self.assertEqual(status(), 200)
        consent.revoke(self.titular, self.patient.pk, "deteccion")
        self.assertEqual(status(), 403)
        link = Client().post(
            f"/api/v1/patients/{self.patient.pk}/nodes",
            data=json.dumps({"name": "Otra"}),
            content_type="application/json",
            HTTP_X_SESSION_TOKEN=self.api_token(self.titular),
        )
        self.assertEqual(link.status_code, 400)
        self.assertIn("detección", link.json()["error"])


class ExportTests(PrivacyBase):
    def test_account_export_has_no_secrets_nor_foreign_file(self):
        self.posture(self.cuidador)
        MobileDevice.objects.create(
            user=self.cuidador,
            installation_id="00000000-0000-0000-0000-000000000001",
            token="device-token-secret-value",
            platform="android",
            session_key="session-secret-value",
        )
        response = self.web(self.cuidador).post(reverse("PrivacidadApp:export_account"))
        self.assertIn("attachment", response["Content-Disposition"])
        body = response.content.decode()
        for secret in ("device-token-secret-value", "session-secret-value", "credential_hash"):
            self.assertNotIn(secret, body)
        data = json.loads(body)
        self.assertEqual(data["account"]["username"], "cuidador")
        self.assertEqual(len(data["authored_records"]), 1)
        self.assertNotIn("Rosa Demo", body)  # the patient file belongs to the titular
        self.assertEqual(PrivacyOperation.objects.get().kind, "export_account")

    def test_patient_export_is_titular_only(self):
        self.posture(self.cuidador)
        url = reverse("PrivacidadApp:export_patient", args=[self.patient.pk])
        self.assertEqual(self.web(self.cuidador).post(url).status_code, 403)
        self.assertEqual(self.web(self.person("ajeno")).post(url).status_code, 404)
        data = json.loads(self.web(self.titular).post(url).content)
        self.assertEqual(data["patient"]["name"], "Rosa Demo")
        self.assertEqual(data["records"][0]["author"], "Cuidador")
        self.assertEqual(data["consents"][0]["scope"], "cuidado")


def references_to(instance):
    """Rows in any model pointing to `instance` through a foreign key."""
    found = {}
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if getattr(field, "many_to_one", False) and field.related_model is type(instance):
                count = model.objects.filter(**{field.name: instance.pk}).count()
                if count:
                    found[f"{model.__name__}.{field.name}"] = count
    return found


class EraseTests(PrivacyBase):
    def test_delete_patient_needs_exact_name_and_removes_everything(self):
        first = self.posture(self.cuidador)
        for note in ("Primera corrección", "Corrección de la corrección"):
            token = services.action_token(self.titular, self.patient, "correction", first.pk)
            first = services.correct_event(self.titular, self.patient.pk, first.pk, token, note)
        invitations.create_invitation(self.titular, self.patient.pk, "familiar")
        with self.assertRaises(ValidationError):
            erase.delete_patient(self.titular, self.patient.pk, "Otra persona")
        response = self.web(self.cuidador).post(
            reverse("PrivacidadApp:delete_patient", args=[self.patient.pk]),
            {"typed_name": "Rosa Demo"},
        )
        self.assertEqual(response.status_code, 403)
        patient = self.patient
        self.web(self.titular).post(
            reverse("PrivacidadApp:delete_patient", args=[patient.pk]),
            {"typed_name": " rosa demo "},
        )
        self.assertFalse(Patient.objects.filter(pk=patient.pk).exists())
        self.assertEqual(references_to(patient), {})
        self.assertEqual(PrivacyOperation.objects.get().counts["records"], 3)

    def test_caregiver_erases_account_and_keeps_anonymous_authorship(self):
        event = self.posture(self.cuidador)
        with self.assertRaises(ValidationError):
            erase.erase_account(self.cuidador, "incorrecta")
        self.assertTrue(User.objects.get(pk=self.cuidador.pk).is_active)
        token = self.api_token(self.cuidador)
        client = self.web(self.cuidador)
        client.post(reverse("PrivacidadApp:delete_account"), {"password": PASSWORD})
        user = User.objects.get(pk=self.cuidador.pk)
        self.assertFalse(user.is_active or user.email or user.first_name)
        self.assertTrue(user.username.startswith("eliminado-"))
        self.assertFalse(EmailAddress.objects.filter(user=user).exists())
        self.assertFalse(AccountConsent.objects.filter(user=user).exists())
        self.assertEqual(Client().get("/api/v1/me", HTTP_X_SESSION_TOKEN=token).status_code, 401)
        self.assertFalse(Client().login(username="cuidador", password=PASSWORD))
        event.refresh_from_db()
        history = self.web(self.titular).get(reverse("CuidadosApp:history", args=[self.patient.pk]))
        self.assertContains(history, "Registrado por Cuenta eliminada")
        panel = self.web(self.titular).get(reverse("CuidadosApp:panel"))
        self.assertContains(panel, "registrada por Cuenta eliminada")
        self.assertIsNone(access.role_for(user, self.patient))

    def test_titular_erasure_takes_patients_and_cuts_links(self):
        self.posture(self.cuidador)
        erase.erase_account(self.titular, PASSWORD)
        self.assertFalse(Patient.objects.exists())
        self.assertFalse(PatientAccess.objects.exists())
        self.assertFalse(CareEvent.objects.exists())
        self.assertEqual(self.web(self.cuidador).get(reverse("CuidadosApp:patients")).status_code, 200)


class PurgeTests(PrivacyBase):
    def test_purge_deletes_only_expired_and_reports_counts(self):
        now = timezone.now()
        node = DetectionNode.objects.create(patient=self.patient, name="Cámara", credential_hash="q" * 64)

        def observation(days, risk):
            row = PostureObservation.objects.create(
                node=node,
                event_id=f"00000000-0000-0000-0000-{days:06d}{len(risk):06d}",
                observed_at=now - timedelta(days=days),
                posture="supina",
                confidence=0.5,
                model_version="m",
                rule_version="r",
                risk=risk,
                payload_hash="p" * 64,
            )
            return row.pk

        keep = [observation(10, ""), observation(200, "fall")]
        drop = [observation(40, ""), observation(400, "fall")]
        attempt = AccessCodeAttempt.objects.create(user=self.cuidador)
        AccessCodeAttempt.objects.filter(pk=attempt.pk).update(created_at=now - timedelta(days=2))
        AccessCodeAttempt.objects.create(user=self.cuidador)
        old = Patient.objects.create(owner=self.titular, name="Archivado Antiguo", active=False, archived_at=now - timedelta(days=800))
        recent = Patient.objects.create(owner=self.titular, name="Archivado Reciente", active=False, archived_at=now - timedelta(days=10))

        out = StringIO()
        call_command("purge_expired_data", "--dry-run", stdout=out)
        self.assertIn("observations_without_risk=1", out.getvalue())
        self.assertIn("archived_patients=1", out.getvalue())
        self.assertEqual(PostureObservation.objects.count(), 4)

        out = StringIO()
        call_command("purge_expired_data", stdout=out)
        self.assertNotIn("Archivado", out.getvalue())
        self.assertEqual(set(PostureObservation.objects.values_list("pk", flat=True)), set(keep))
        self.assertFalse(PostureObservation.objects.filter(pk__in=drop).exists())
        self.assertEqual(AccessCodeAttempt.objects.count(), 1)
        self.assertFalse(Patient.objects.filter(pk=old.pk).exists())
        self.assertTrue(Patient.objects.filter(pk=recent.pk).exists())
        self.assertTrue(Patient.objects.filter(pk=self.patient.pk).exists())
        operation = PrivacyOperation.objects.get(kind="purge")
        self.assertNotIn("Archivado", json.dumps(operation.counts))
