"""Spec 013: delegated care by role (titular, familiar, cuidador)."""

import json
import sys
import types
import uuid
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.http import Http404
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from PlanesApp.models import Plan, Subscription

from . import access, invitations, services
from .management.commands.send_mobile_reminders import RISK_MESSAGES
from .models import (
    AccessCodeAttempt,
    CareEvent,
    CareGuide,
    CareTask,
    DetectionNode,
    Patient,
    PatientAccess,
    PatientInvitation,
    PostureObservation,
)
from .scheduling import agenda, reminders

PASSWORD = "Demo-strong-123!"


class DelegatedCareBase(TestCase):
    def setUp(self):
        cache.clear()  # allauth login rate limits must not leak between tests
        self.titular = self.person("titular")
        self.familiar = self.person("familiar")
        self.cuidador = self.person("cuidador")
        self.stranger = self.person("ajeno")
        self.root = User.objects.create_superuser("root", "root@example.test", PASSWORD)
        self.patient = Patient.objects.create(owner=self.titular, name="Paciente demo")
        self.link(self.familiar, access.FAMILIAR)
        self.care_link = self.link(self.cuidador, access.CUIDADOR)

    def person(self, name):
        user = User.objects.create_user(
            name, f"{name}@example.test", PASSWORD, first_name=name.capitalize()
        )
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )
        return user

    def link(self, user, role, patient=None):
        return PatientAccess.objects.create(
            patient=patient or self.patient, user=user, role=role
        )

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
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["meta"]["session_token"]

    def everyone(self):
        return {
            "titular": self.titular,
            "familiar": self.familiar,
            "cuidador": self.cuidador,
            "ajeno": self.stranger,
            "root": self.root,
        }


class AccessMatrixTests(DelegatedCareBase):
    def test_web_matrix_by_role(self):
        pk = self.patient.pk
        cases = [
            ("get", reverse("CuidadosApp:patient", args=[pk]), (200, 200, 200)),
            ("get", reverse("CuidadosApp:patient_edit", args=[pk]), (200, 200, 403)),
            ("get", reverse("CuidadosApp:medication_new", args=[pk]), (200, 200, 403)),
            ("get", reverse("CuidadosApp:history", args=[pk]), (200, 200, 403)),
            ("get", reverse("CuidadosApp:posture", args=[pk]), (200, 200, 200)),
            ("get", reverse("CuidadosApp:timer", args=[pk]), (200, 200, 200)),
            ("post", reverse("CuidadosApp:archive", args=[pk]), (302, 403, 403)),
            ("post", reverse("CuidadosApp:access", args=[pk]), (200, 403, 403)),
            ("post", reverse("CuidadosApp:leave", args=[pk]), (403, 302, 302)),
        ]
        for method, url, (titular, familiar, cuidador) in cases:
            for name, expected in (
                ("titular", titular),
                ("familiar", familiar),
                ("cuidador", cuidador),
                ("ajeno", 404),
                ("root", 404),
            ):
                # Fresh links: the leave case above revokes them for the next URL.
                PatientAccess.objects.filter(revoked_at__isnull=False).delete()
                if not PatientAccess.objects.filter(user=self.familiar).exists():
                    self.link(self.familiar, access.FAMILIAR)
                if not PatientAccess.objects.filter(user=self.cuidador).exists():
                    self.link(self.cuidador, access.CUIDADOR)
                with self.subTest(url=url, user=name):
                    client = self.web(self.everyone()[name])
                    response = getattr(client, method)(url, {"role": "cuidador"})
                    self.assertEqual(response.status_code, expected)
        self.patient.refresh_from_db()
        self.assertTrue(self.patient.active)

    def test_api_matrix_by_role_without_side_effects(self):
        self.premium(self.titular)
        node = DetectionNode.objects.create(
            patient=self.patient, name="Cámara", credential_hash="x" * 64
        )
        pk = self.patient.pk
        cases = [
            ("get", f"patients/{pk}", (200, 200, 200)),
            ("get", f"patients/{pk}/summary", (200, 200, 200)),
            ("get", f"patients/{pk}/daily/medications", (200, 200, 200)),
            ("get", f"patients/{pk}/history", (200, 200, 403)),
            ("get", f"patients/{pk}/observations", (200, 200, 403)),
            ("get", f"patients/{pk}/nodes", (200, 403, 403)),
            ("get", f"patients/{pk}/access", (200, 403, 403)),
            ("post", f"patients/{pk}/daily/tasks", (201, 201, 403)),
            ("post", f"patients/{pk}/access", (201, 403, 403)),
        ]
        tokens = {name: self.api_token(user) for name, user in self.everyone().items()}
        for method, path, (titular, familiar, cuidador) in cases:
            for name, expected in (
                ("titular", titular),
                ("familiar", familiar),
                ("cuidador", cuidador),
                ("ajeno", 404),
                ("root", 404),
            ):
                with self.subTest(path=path, user=name):
                    before = (CareTask.objects.count(), PatientInvitation.objects.count())
                    kwargs = {"HTTP_X_SESSION_TOKEN": tokens[name]}
                    if method == "post":
                        body = {"role": "cuidador", "name": f"Hidratación {name}", "active": True}
                        response = Client().post(
                            "/api/v1/" + path,
                            data=json.dumps(body),
                            content_type="application/json",
                            **kwargs,
                        )
                    else:
                        response = Client().get("/api/v1/" + path, **kwargs)
                    self.assertEqual(response.status_code, expected, response.content)
                    if expected >= 400:
                        self.assertEqual(
                            before,
                            (CareTask.objects.count(), PatientInvitation.objects.count()),
                        )
        # QA-2026-10-22-08: revoking a node of someone else's patient is a 404.
        for name in ("ajeno", "root", "familiar", "cuidador"):
            response = Client().post(
                f"/api/v1/nodes/{node.pk}/revoke",
                data="{}",
                content_type="application/json",
                HTTP_X_SESSION_TOKEN=tokens[name],
            )
            self.assertIn(response.status_code, (403, 404))
        node.refresh_from_db()
        self.assertTrue(node.active)

    def test_patient_list_reports_role_and_actions(self):
        response = Client().get(
            "/api/v1/patients", HTTP_X_SESSION_TOKEN=self.api_token(self.cuidador)
        )
        [item] = response.json()["patients"]
        self.assertEqual(item["role"], "cuidador")
        self.assertNotIn("configure", item["allowed_actions"])
        self.assertIn("record", item["allowed_actions"])
        detail = Client().get(
            f"/api/v1/patients/{self.patient.pk}",
            HTTP_X_SESSION_TOKEN=self.api_token(self.cuidador),
        ).json()
        self.assertNotIn("archive", detail["tokens"])

    def test_lists_include_patients_of_two_titulars(self):
        other = self.person("otra")
        second = Patient.objects.create(owner=other, name="Segunda familia")
        self.link(self.cuidador, access.CUIDADOR, second)
        own = Patient.objects.create(owner=self.cuidador, name="Propio")
        self.assertEqual(
            set(access.active_ids_for(self.cuidador)),
            {self.patient.pk, second.pk, own.pk},
        )
        page = self.web(self.cuidador).get(reverse("CuidadosApp:patients"))
        self.assertContains(page, "Segunda familia")
        self.assertContains(page, "Paciente demo")


class DelegatedRecordTests(DelegatedCareBase):
    def setUp(self):
        super().setUp()
        self.task = CareTask.objects.create(patient=self.patient, name="Hidratación")
        self.guide = CareGuide.objects.filter(category="posture", active=True).first()

    def agenda_token(self, user):
        [item] = [i for i in agenda(user) if i["object"] == self.task]
        return item["token"]

    def test_caregiver_is_the_author_and_occurrence_is_recorded_once(self):
        event = services.record_daily(
            self.cuidador, self.patient.pk, self.agenda_token(self.cuidador), "done", ""
        )
        self.assertEqual(event.author, self.cuidador)
        with self.assertRaises(ValidationError):
            services.record_daily(
                self.titular, self.patient.pk, self.agenda_token(self.titular), "done", ""
            )
        self.assertEqual(CareEvent.objects.count(), 1)

    def test_panel_shows_who_recorded_each_activity(self):
        services.record_daily(
            self.cuidador, self.patient.pk, self.agenda_token(self.cuidador), "done", ""
        )
        services.record_posture(
            self.cuidador,
            self.patient.pk,
            services.action_token(self.cuidador, self.patient, "posture"),
            self.guide,
            120,
        )
        panel = self.web(self.titular).get(reverse("CuidadosApp:panel"))
        self.assertContains(panel, "Hecho por Cuidador")
        self.assertContains(panel, "registrada por Cuidador")

    def test_titular_capacity_and_archive_govern_the_caregiver(self):
        Patient.objects.filter(pk=self.patient.pk).update(active=False)
        token = services.action_token(self.cuidador, self.patient, "posture")
        with self.assertRaises(ValidationError):
            services.record_posture(self.cuidador, self.patient.pk, token, self.guide, 120)

    def test_links_do_not_use_either_capacity(self):
        # Free allows one active patient; links count for neither side (D-050 a).
        from .capacity import capacity_state

        own = services.save_patient(self.cuidador, {"name": "Propio del cuidador"})
        self.assertEqual(own.owner, self.cuidador)
        self.assertEqual(capacity_state(self.cuidador)["count"], 1)
        self.assertEqual(capacity_state(self.titular)["count"], 1)
        self.assertEqual(capacity_state(self.titular)["limit"], 1)

    def test_revocation_stops_actions_and_keeps_authorship(self):
        posture = services.record_posture(
            self.cuidador,
            self.patient.pk,
            services.action_token(self.cuidador, self.patient, "posture"),
            self.guide,
            120,
        )
        stale = services.action_token(self.cuidador, self.patient, "posture", version=1)
        invitations.revoke_access(self.titular, self.care_link.pk)
        with self.assertRaises(Http404):
            services.record_posture(self.cuidador, self.patient.pk, stale, self.guide, 120)
        posture.refresh_from_db()
        self.assertEqual(posture.author, self.cuidador)
        self.assertEqual(
            self.web(self.cuidador).get(reverse("CuidadosApp:patient", args=[self.patient.pk])).status_code,
            404,
        )

    def test_caregiver_corrects_only_own_records(self):
        mine = services.record_posture(
            self.cuidador,
            self.patient.pk,
            services.action_token(self.cuidador, self.patient, "posture"),
            self.guide,
            120,
        )
        theirs = services.record_posture(
            self.titular,
            self.patient.pk,
            services.action_token(self.titular, self.patient, "posture", version=1),
            self.guide,
            120,
        )
        token = services.action_token(self.cuidador, self.patient, "correction", mine.pk)
        services.correct_event(self.cuidador, self.patient.pk, mine.pk, token, "Fue a las 10")
        token = services.action_token(self.cuidador, self.patient, "correction", theirs.pk)
        with self.assertRaises(PermissionDenied):
            services.correct_event(self.cuidador, self.patient.pk, theirs.pk, token, "No")

    def test_family_configures_but_cannot_archive(self):
        page = self.web(self.familiar).get(reverse("CuidadosApp:patient", args=[self.patient.pk]))
        self.assertContains(page, "Agregar medicamento")
        self.assertNotContains(page, "Confirmar archivo")
        caregiver = self.web(self.cuidador).get(reverse("CuidadosApp:patient", args=[self.patient.pk]))
        self.assertNotContains(caregiver, "Agregar medicamento")
        self.assertNotContains(caregiver, "Ver historial")
        self.assertContains(caregiver, "Dejar de acompañar")


class InvitationTests(DelegatedCareBase):
    def setUp(self):
        super().setUp()
        PatientAccess.objects.all().delete()

    def test_code_is_single_use_and_stored_hashed(self):
        invitation, code = invitations.create_invitation(
            self.titular, self.patient.pk, access.CUIDADOR
        )
        self.assertNotIn(invitations.normalize(code), invitation.code_hash)
        self.assertEqual(
            invitations.preview(self.cuidador, code.lower()),
            {"patient_name": "Paciente demo", "role": "cuidador"},
        )
        link = invitations.accept(self.cuidador, code)
        self.assertEqual((link.user, link.role), (self.cuidador, "cuidador"))
        with self.assertRaisesMessage(ValidationError, invitations.INVALID):
            invitations.accept(self.familiar, code)

    def test_own_and_duplicate_codes_are_rejected_without_consuming(self):
        _, code = invitations.create_invitation(self.titular, self.patient.pk, access.FAMILIAR)
        with self.assertRaises(ValidationError):
            invitations.accept(self.titular, code)
        self.link(self.familiar, access.FAMILIAR)
        with self.assertRaises(ValidationError):
            invitations.accept(self.familiar, code)
        self.assertEqual(invitations.pending(self.patient).count(), 1)
        invitations.accept(self.cuidador, code)

    def test_expired_and_revoked_codes_share_the_generic_message(self):
        expired, old = invitations.create_invitation(self.titular, self.patient.pk, access.CUIDADOR)
        PatientInvitation.objects.filter(pk=expired.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        revoked, gone = invitations.create_invitation(self.titular, self.patient.pk, access.CUIDADOR)
        invitations.revoke_invitation(self.titular, revoked.pk)
        for code in (old, gone, "ABCDE-FGHJK"):
            with self.assertRaisesMessage(ValidationError, invitations.INVALID):
                invitations.preview(self.cuidador, code)
        self.assertFalse(PatientAccess.objects.exists())

    def test_failed_attempts_are_limited(self):
        _, code = invitations.create_invitation(self.titular, self.patient.pk, access.CUIDADOR)
        for _ in range(invitations.MAX_FAILURES):
            with self.assertRaises(ValidationError):
                invitations.preview(self.cuidador, "ZZZZZ-ZZZZZ")
        with self.assertRaisesMessage(ValidationError, "demasiados intentos"):
            invitations.accept(self.cuidador, code)
        AccessCodeAttempt.objects.update(created_at=timezone.now() - timedelta(minutes=16))
        invitations.accept(self.cuidador, code)

    def test_unverified_email_and_pending_limit(self):
        EmailAddress.objects.filter(user=self.cuidador).update(verified=False)
        _, code = invitations.create_invitation(self.titular, self.patient.pk, access.CUIDADOR)
        with self.assertRaisesMessage(ValidationError, "Verifica tu correo"):
            invitations.accept(self.cuidador, code)
        for _ in range(invitations.MAX_PENDING - 1):
            invitations.create_invitation(self.titular, self.patient.pk, access.CUIDADOR)
        with self.assertRaises(ValidationError):
            invitations.create_invitation(self.titular, self.patient.pk, access.CUIDADOR)

    def test_web_join_flow_previews_then_confirms(self):
        _, code = invitations.create_invitation(self.titular, self.patient.pk, access.FAMILIAR)
        client = self.web(self.familiar)
        preview = client.post(reverse("CuidadosApp:join"), {"code": code})
        self.assertContains(preview, "Paciente demo")
        self.assertFalse(PatientAccess.objects.exists())
        done = client.post(reverse("CuidadosApp:join"), {"code": code, "confirm": "1"})
        self.assertRedirects(done, reverse("CuidadosApp:patient", args=[self.patient.pk]))
        self.assertEqual(PatientAccess.objects.get().role, "familiar")

    def test_web_code_page_and_leave(self):
        page = self.web(self.titular).post(
            reverse("CuidadosApp:access", args=[self.patient.pk]), {"role": "cuidador"}
        )
        self.assertContains(page, "Código para un cuidador")
        code = page.context["code"]
        invitations.accept(self.cuidador, code)
        self.web(self.cuidador).post(reverse("CuidadosApp:leave", args=[self.patient.pk]))
        self.assertIsNotNone(PatientAccess.objects.get().revoked_at)
        self.assertEqual(access.role_for(self.cuidador, self.patient), None)

    def test_api_accept_flow(self):
        _, code = invitations.create_invitation(self.titular, self.patient.pk, access.CUIDADOR)
        token = self.api_token(self.cuidador)
        response = Client().post(
            "/api/v1/access/accept",
            data=json.dumps({"code": code}),
            content_type="application/json",
            HTTP_X_SESSION_TOKEN=token,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"patient_id": self.patient.pk, "role": "cuidador"})


class RecipientTests(DelegatedCareBase):
    def test_care_reminders_go_to_titular_and_caregiver(self):
        CareTask.objects.create(
            patient=self.patient,
            name="Curación",
            time=(timezone.localtime() - timedelta(hours=1)).time().replace(second=0, microsecond=0),
        )
        CareTask.objects.update(schedule_effective_at=timezone.now() - timedelta(days=1))
        self.assertTrue(reminders(self.titular))
        self.assertTrue(reminders(self.cuidador))
        self.assertFalse(reminders(self.familiar))

    def test_risk_alerts_reach_every_role_on_titular_plan(self):
        self.assertEqual(access.risk_patient_ids(self.cuidador), [])
        self.premium(self.titular)
        for user in (self.titular, self.familiar, self.cuidador):
            self.assertEqual(access.risk_patient_ids(user), [self.patient.pk])
        self.assertEqual(access.risk_patient_ids(self.stranger), [])
        invitations.revoke_access(self.titular, self.care_link.pk)
        self.assertEqual(access.risk_patient_ids(self.cuidador), [])

    @override_settings(VIGIA_PUSH_ENABLED=True)
    def test_push_command_sends_fall_to_family_and_caregiver(self):
        self.premium(self.titular)
        node = DetectionNode.objects.create(
            patient=self.patient, name="Cámara", credential_hash="y" * 64
        )
        PostureObservation.objects.create(
            node=node,
            event_id=uuid.uuid4(),
            observed_at=timezone.now(),
            posture="indeterminada",
            confidence=0,
            model_version="test",
            rule_version="fall-v1",
            risk="fall",
            payload_hash="z" * 64,
        )
        for user in (self.titular, self.familiar, self.cuidador, self.stranger):
            Client().post(
                "/api/v1/devices",
                data=json.dumps(
                    {
                        "installation_id": str(uuid.uuid4()),
                        "token": f"device-token-not-real-{user.username}",
                        "platform": "android",
                        "enabled": True,
                    }
                ),
                content_type="application/json",
                HTTP_X_SESSION_TOKEN=self.api_token(user),
            )
        sent = []
        messaging = types.SimpleNamespace(
            Message=lambda **kw: kw,
            Notification=lambda **kw: kw,
            AndroidConfig=lambda **kw: kw, AndroidNotification=lambda **kw: kw,
            send=sent.append,
        )
        modules = {
            "firebase_admin": types.SimpleNamespace(_apps=[object()], messaging=messaging),
            "firebase_admin.messaging": messaging,
            "firebase_admin.exceptions": types.SimpleNamespace(FirebaseError=Exception),
        }
        with patch.dict(sys.modules, modules):
            for _ in range(2):
                call_command("send_mobile_reminders", stdout=StringIO(), stderr=StringIO())
        falls = sorted(
            m["token"].rsplit("-", 1)[1] for m in sent if m["notification"]["body"] == RISK_MESSAGES["fall"]
        )
        self.assertEqual(
            falls, ["cuidador", "familiar", "titular"]
        )
