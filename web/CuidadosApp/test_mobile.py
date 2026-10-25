import json
import sys
import types
import uuid
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.core.cache import cache
from django.utils import timezone

from PlanesApp.models import Plan, Subscription

from .management.commands.send_mobile_reminders import RISK_MESSAGES
from .models import CareEvent, MobileDevice, Patient, PostureObservation, PostureTimer


class MobileTests(TestCase):
    def setUp(self):
        cache.clear()  # Rate-limit state must not leak between independent test logins.
        self.user = User.objects.create_user(
            "movil", "movil@example.test", "Demo-strong-123!"
        )
        self.other = User.objects.create_user(
            "otro", "otro@example.test", "Demo-strong-123!"
        )
        self.patient = Patient.objects.create(owner=self.user, name="Paciente demo")
        self.foreign = Patient.objects.create(owner=self.other, name="Privado")
        self.client = Client(enforce_csrf_checks=True)
        r = self.client.post(
            "/_allauth/app/v1/auth/login",
            data=json.dumps({"username": "movil", "password": "Demo-strong-123!"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        self.token = r.json()["meta"]["session_token"]
        self.headers = {"HTTP_X_SESSION_TOKEN": self.token}

    def get(self, path):
        return self.client.get("/api/v1/" + path, **self.headers)

    def post(self, path, data):
        return self.client.post(
            "/api/v1/" + path,
            data=json.dumps(data),
            content_type="application/json",
            **self.headers,
        )

    def premium(self):
        plan = Plan.objects.get(code="pro")
        Subscription.objects.update_or_create(
            user=self.user,
            defaults={
                "plan": plan,
                "plan_name": plan.name,
                "amount_clp": plan.amount_clp,
                "start": timezone.now() - timedelta(days=1),
                "end": timezone.now() + timedelta(days=29),
            },
        )

    def test_header_only_and_logout(self):
        self.assertEqual(self.get("me").status_code, 200)
        cookie_client = Client()
        cookie_client.force_login(self.user)
        self.assertEqual(cookie_client.get("/api/v1/me").status_code, 401)
        r = self.client.delete("/_allauth/app/v1/auth/session", **self.headers)
        self.assertIn(r.status_code, (200, 401))
        self.assertEqual(self.get("me").status_code, 401)

    def test_inactive_and_password_change_revoke(self):
        self.user.set_password("new-strong-password!")
        self.user.save()
        self.assertEqual(self.get("me").status_code, 401)

    def test_private_and_root_no_exception(self):
        self.assertEqual(self.get(f"patients/{self.foreign.pk}").status_code, 404)
        self.user.is_superuser = True
        self.user.save()
        self.assertEqual(
            self.get(f"patients/{self.foreign.pk}/history").status_code, 404
        )
        self.assertEqual(
            self.get("patients").json()["patients"][0]["id"], self.patient.pk
        )

    def test_plan_capacity_and_edit(self):
        self.assertFalse(
            self.get("capabilities").json()["features"]["posture_detection"]
        )
        r = self.post("patients", {"name": "Segundo"})
        self.assertEqual(r.status_code, 400)
        r = self.post(
            f"patients/{self.patient.pk}", {"name": "Actualizado", "version": 0}
        )
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(
            self.post(
                f"patients/{self.patient.pk}", {"name": "Anterior", "version": 0}
            ).status_code,
            400,
        )

    def test_daily_event_idempotency_and_correction(self):
        r = self.post(
            f"patients/{self.patient.pk}/daily/tasks",
            {
                "name": "Higiene",
                "notes": "",
                "time": "",
                "active": True,
                "start_date": "",
                "end_date": "",
            },
        )
        self.assertEqual(r.status_code, 201, r.content)
        item = self.get("agenda").json()["items"][0]
        d = {"token": item["token"], "status": "done", "note": ""}
        self.assertEqual(
            self.post(f"patients/{self.patient.pk}/events", d).status_code, 200
        )
        self.assertEqual(
            self.post(f"patients/{self.patient.pk}/events", d).status_code, 200
        )
        self.assertEqual(CareEvent.objects.count(), 1)
        hist = self.get(f"patients/{self.patient.pk}/history").json()["items"][0]
        self.assertEqual(
            self.post(
                f"patients/{self.patient.pk}/history/{hist['id']}/correction",
                {"token": hist["token"], "note": "Se realizó después"},
            ).status_code,
            200,
        )
        self.assertEqual(CareEvent.objects.count(), 2)

    def test_medication_and_posture_use_existing_rules(self):
        r = self.post(
            f"patients/{self.patient.pk}/daily/medications",
            {
                "name": "Medicamento demo",
                "dose": "Indicada",
                "notes": "",
                "hours": "25:00",
                "active": True,
            },
        )
        self.assertEqual(r.status_code, 400)
        guide = next(
            g for g in self.get("guides").json()["items"] if g["code"] == "supina"
        )
        detail = self.get(f"patients/{self.patient.pk}").json()
        d = {
            "token": detail["tokens"]["posture"],
            "guide": guide["id"],
            "interval": 60,
            "note": "",
        }
        self.assertEqual(
            self.post(f"patients/{self.patient.pk}/posture", d).status_code, 200
        )
        self.assertEqual(PostureTimer.objects.get(patient=self.patient).interval, 60)

    def test_edge_plan_revocation_dedup_and_no_clinical_event(self):
        path = f"patients/{self.patient.pk}/nodes"
        self.assertEqual(self.post(path, {"name": "Cámara demo"}).status_code, 403)
        self.premium()
        node = self.post(path, {"name": "Cámara demo"}).json()
        headers = {"HTTP_AUTHORIZATION": "Bearer " + node["credential"]}
        data = {
            "event_id": str(uuid.uuid4()),
            "observed_at": timezone.now().isoformat(),
            "posture": "supina",
            "confidence": 0.9,
            "model_version": "test",
            "rule_version": "calibrated-v1",
            "risk": "",
        }

        def send(d):
            return self.client.post(
                "/api/v1/edge/observations",
                data=json.dumps(d),
                content_type="application/json",
                **headers,
            )

        self.assertEqual(send(data).status_code, 201)
        self.assertEqual(send(data).status_code, 200)
        self.assertEqual(send({**data, "confidence": 0.8}).status_code, 409)
        self.assertEqual(send({**data, "image": "forbidden"}).status_code, 400)
        self.assertEqual(PostureObservation.objects.count(), 1)
        self.assertEqual(CareEvent.objects.count(), 0)
        Subscription.objects.filter(user=self.user).update(
            end=timezone.now() - timedelta(seconds=1)
        )
        self.assertFalse(
            self.get("capabilities").json()["features"]["posture_detection"]
        )
        self.assertEqual(send({**data, "event_id": str(uuid.uuid4())}).status_code, 403)
        self.assertEqual(
            self.get(f"patients/{self.patient.pk}/observations").status_code, 200
        )
        self.premium()
        self.assertEqual(self.post(f"nodes/{node['id']}/revoke", {}).status_code, 200)
        self.assertEqual(send(data).status_code, 401)

    def edge_node(self):
        self.premium()
        node = self.post(f"patients/{self.patient.pk}/nodes", {"name": "Cámara demo"}).json()

        def send(**changes):
            data = {
                "event_id": str(uuid.uuid4()),
                "observed_at": timezone.now().isoformat(),
                "posture": "indeterminada",
                "confidence": 0,
                "model_version": "test",
                "rule_version": "fall-v1",
                "risk": "fall",
                **changes,
            }
            return self.client.post(
                "/api/v1/edge/observations",
                data=json.dumps(data),
                content_type="application/json",
                HTTP_AUTHORIZATION="Bearer " + node["credential"],
            )

        return send

    def test_edge_fall_is_stored_in_history_with_reception_time(self):
        send = self.edge_node()
        with self.assertLogs("vigia.edge", "WARNING") as logs:
            self.assertEqual(send().status_code, 201)
        self.assertIn("Riesgo fall recibido", logs.output[0])
        self.assertEqual(send(posture="supina", confidence=0.7).status_code, 201)
        self.assertEqual(send(risk="immobility").status_code, 400)
        self.assertEqual(send(risk="caida").status_code, 400)
        self.assertEqual(send(image="forbidden").status_code, 400)
        item = self.get(f"patients/{self.patient.pk}/observations").json()["items"][-1]
        self.assertEqual((item["risk"], item["posture"]), ("fall", "indeterminada"))
        self.assertIsNotNone(item["received_at"])
        self.assertEqual(PostureObservation.objects.filter(risk="fall").count(), 2)
        self.assertFalse(CareEvent.objects.exists())

    def push_runs(self, runs, failures=0):
        """Runs the push command with a fake Firebase; the first `failures` sends fail."""
        self.post("devices", {"installation_id": str(uuid.uuid4()),
                              "token": "example-device-token-not-real", "platform": "android", "enabled": True})
        sent, state = [], {"failures": failures}

        class FirebaseError(Exception):
            pass

        def deliver(message):
            if state["failures"]:
                state["failures"] -= 1
                raise FirebaseError("no disponible")
            sent.append(message)

        messaging = types.SimpleNamespace(
            Message=lambda **kw: kw, Notification=lambda **kw: kw,
            AndroidConfig=lambda **kw: kw, AndroidNotification=lambda **kw: kw, send=deliver,
        )
        firebase = types.SimpleNamespace(_apps=[object()], messaging=messaging)
        exceptions = types.SimpleNamespace(FirebaseError=FirebaseError)
        modules = {"firebase_admin": firebase, "firebase_admin.messaging": messaging,
                   "firebase_admin.exceptions": exceptions}
        errors = StringIO()
        with patch.dict(sys.modules, modules):
            for _ in range(runs):
                call_command("send_mobile_reminders", stdout=StringIO(), stderr=errors)
        risks = [m for m in sent if m["notification"]["body"] in RISK_MESSAGES.values()]
        return risks, errors.getvalue()

    @override_settings(VIGIA_PUSH_ENABLED=True)
    def test_fall_push_uses_existing_channel_once_and_first(self):
        send = self.edge_node()
        self.assertEqual(send(risk="immobility", posture="supina", confidence=0.8).status_code, 201)
        self.assertEqual(send().status_code, 201)
        risks, _ = self.push_runs(2)
        # Two calls, one push per risk: receipts prevent duplicates; falls go first.
        self.assertEqual(len(risks), 2)
        self.assertEqual(risks[0]["notification"]["body"], RISK_MESSAGES["fall"])
        # D-058: same generic text; private on the lock screen; only falls are urgent.
        private = {"visibility": "private"}
        self.assertEqual(risks[0]["android"], {"priority": "high", "notification": private})
        self.assertEqual(risks[1]["android"], {"priority": None, "notification": private})

    @override_settings(VIGIA_PUSH_ENABLED=True)
    def test_late_or_failed_risk_push_is_retried_until_delivered_once(self):
        # QA-2026-10-22-02: no fixed 2-minute window; an FCM failure is retried.
        send = self.edge_node()
        late = timezone.now() - timedelta(minutes=30)
        self.assertEqual(send(observed_at=late.isoformat()).status_code, 201)
        self.assertEqual(
            send(risk="immobility", posture="supina", confidence=0.8).status_code, 201
        )
        PostureObservation.objects.update(received_at=timezone.now() - timedelta(minutes=10))
        risks, errors = self.push_runs(3, failures=2)
        self.assertIn("Entrega no confirmada", errors)
        bodies = [m["notification"]["body"] for m in risks]
        self.assertEqual(bodies, [RISK_MESSAGES["fall"], RISK_MESSAGES["immobility"]])

    def test_late_risk_is_accepted_but_ordinary_observations_expire(self):
        send = self.edge_node()
        ago = lambda minutes: (timezone.now() - timedelta(minutes=minutes)).isoformat()
        self.assertEqual(send(observed_at=ago(50)).status_code, 201)
        self.assertEqual(send(observed_at=ago(61)).status_code, 400)
        self.assertEqual(
            send(observed_at=ago(5), risk="", posture="supina", confidence=0.7).status_code,
            400,
        )

    @override_settings(VIGIA_PUSH_ENABLED=True)
    def test_risk_older_than_push_window_is_not_announced(self):
        send = self.edge_node()
        self.assertEqual(send().status_code, 201)
        PostureObservation.objects.update(received_at=timezone.now() - timedelta(hours=2))
        risks, _ = self.push_runs(1)
        self.assertEqual(risks, [])

    def test_bad_json_types_and_routes(self):
        self.assertEqual(self.post("patients", []).status_code, 400)
        self.assertEqual(
            self.post(f"patients/{self.patient.pk}/garbage/active", {}).status_code, 404
        )
        self.assertEqual(
            self.get(f"patients/{self.patient.pk}/daily/garbage").status_code, 404
        )

    def test_device_registration_requires_valid_session(self):
        d = {
            "installation_id": str(uuid.uuid4()),
            "token": "example-device-token-not-real",
            "platform": "ios",
            "enabled": True,
        }
        self.assertEqual(self.post("devices", d).status_code, 200)
        self.assertTrue(MobileDevice.objects.get().active)
        self.post("devices", {**d, "enabled": False})
        self.assertFalse(MobileDevice.objects.get().active)

    def test_mfa_pending_does_not_access_api(self):
        from allauth.mfa.adapter import get_adapter
        from allauth.mfa.models import Authenticator

        Authenticator.objects.create(
            user=self.other,
            type=Authenticator.Type.TOTP,
            data={"secret": get_adapter().encrypt("JBSWY3DPEHPK3PXP")},
        )
        r = Client().post(
            "/_allauth/app/v1/auth/login",
            data=json.dumps({"username": "otro", "password": "Demo-strong-123!"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401, r.content)
        pending = r.json()["meta"]["session_token"]
        self.assertEqual(
            Client().get("/api/v1/me", HTTP_X_SESSION_TOKEN=pending).status_code, 401
        )

    def test_phone_snapshots_are_private_idempotent_and_not_care_or_risk(self):
        path = f"patients/{self.patient.pk}/phone-observations"
        data = {
            "event_id": str(uuid.uuid4()), "observed_at": timezone.now().isoformat(),
            "posture": "supina", "confidence": .85, "platform": "android",
            "model_version": "pose-landmarker-lite", "rule_version": "phone-snapshot-v1",
        }
        self.assertEqual(self.get(path).status_code, 403)
        self.assertEqual(self.post(path, data).status_code, 403)
        self.premium()
        self.assertEqual(self.get(path).status_code, 200)
        self.assertEqual(self.post(f"patients/{self.foreign.pk}/phone-observations", data).status_code, 404)
        self.assertEqual(self.post(path, {**data, "image": "not-permitted"}).status_code, 400)
        self.assertEqual(self.post(path, {**data, "risk": "immobility"}).status_code, 400)
        self.assertEqual(self.post(path, {**data, "confidence": float('nan')}).status_code, 400)
        self.assertEqual(self.post(path, data).status_code, 201)
        self.assertTrue(self.post(path, data).json()["duplicate"])
        self.assertEqual(self.post(path, {**data, "posture": "lateral-derecha"}).status_code, 409)
        row = PostureObservation.objects.get(phone_patient=self.patient)
        self.assertIsNone(row.node_id)
        self.assertEqual(row.risk, "")
        self.assertFalse(CareEvent.objects.exists())
        feed = self.get(f"patients/{self.patient.pk}/observations").json()["items"]
        self.assertEqual(feed[0]["source_type"], "phone")
        self.assertEqual(feed[0]["source"], "Teléfono android")
        Subscription.objects.filter(user=self.user).update(end=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.post(path, data).status_code, 403)
        self.assertEqual(self.get(f"patients/{self.patient.pk}/observations").status_code, 200)

    def test_phone_capture_denies_archived_patient_and_expired_timestamp(self):
        self.premium()
        path = f"patients/{self.patient.pk}/phone-observations"
        data = {"event_id": str(uuid.uuid4()), "observed_at": (timezone.now()-timedelta(minutes=3)).isoformat(),
                "posture": "indeterminada", "confidence": 0, "platform": "ios",
                "model_version": "lite", "rule_version": "snapshot"}
        self.assertEqual(self.post(path, data).status_code, 400)
        self.patient.active = False
        self.patient.save(update_fields=['active'])
        self.assertEqual(self.get(path).status_code, 403)
        self.assertEqual(self.post(path, data).status_code, 403)

    def test_start_clock_without_fabricating_care_and_reject_replay(self):
        path = f"patients/{self.patient.pk}"
        token = self.get(path).json()['tokens']['timer']
        payload = {'token': token, 'action': 'start', 'interval': 60}
        self.assertEqual(self.post(path + '/timer', payload).status_code, 200)
        timer = PostureTimer.objects.get(patient=self.patient)
        self.assertIsNone(timer.last_event)
        self.assertFalse(CareEvent.objects.filter(patient=self.patient).exists())
        self.assertEqual(timer.next_due_at - timer.anchor_at, timedelta(minutes=60))
        due = timer.next_due_at
        self.assertEqual(self.post(path + '/timer', payload).status_code, 400)
        timer.refresh_from_db()
        self.assertEqual(timer.next_due_at, due)
        self.assertEqual(self.post(f'patients/{self.foreign.pk}/timer', payload).status_code, 404)
        rows = self.get('timer-schedule').json()['items']
        self.assertEqual([r['id'] for r in rows], [self.patient.pk])
        for action in ['pause', 'resume', 'interval']:
            token = self.get(path).json()['tokens']['timer']
            self.assertEqual(self.post(path+'/timer', {'token': token, 'action': action, 'interval': 90}).status_code, 200)
            if action == 'pause':
                self.assertEqual(self.get('timer-schedule').json()['items'], [])
        self.assertFalse(CareEvent.objects.filter(patient=self.patient).exists())

    def test_clock_invalid_interval_rolls_back_and_schedule_excludes_foreign(self):
        token = self.get(f'patients/{self.patient.pk}').json()['tokens']['timer']
        self.assertEqual(self.post(f'patients/{self.patient.pk}/timer',
            {'token': token, 'action': 'start', 'interval': 3}).status_code, 400)
        self.assertFalse(PostureTimer.objects.filter(patient=self.patient).exists())
        PostureTimer.objects.create(patient=self.foreign, next_due_at=timezone.now()+timedelta(hours=1))
        self.assertEqual(self.get('timer-schedule').json()['items'], [])

    def test_clock_actions_without_clock_are_rejected_not_missing(self):
        path = f"patients/{self.patient.pk}"
        detail = self.get(path).json()
        self.assertIsNone(detail["timer"])
        for action in ("pause", "resume", "interval"):
            r = self.post(path + "/timer", {"token": detail["tokens"]["timer"],
                "action": action, "interval": 60})
            self.assertEqual(r.status_code, 400, r.content)
        self.assertFalse(PostureTimer.objects.filter(patient=self.patient).exists())

    def test_schedule_follows_posture_and_archive(self):
        path = f"patients/{self.patient.pk}"
        token = self.get(path).json()["tokens"]["timer"]
        self.post(path + "/timer", {"token": token, "action": "start", "interval": 120})
        first = self.get("timer-schedule").json()["items"][0]
        guide = self.get("guides").json()["items"]
        guide = next(g for g in guide if g["category"] == "posture")
        token = self.get(path).json()["tokens"]["posture"]
        r = self.post(path + "/posture", {"token": token, "guide": guide["id"],
            "interval": 60, "note": ""})
        self.assertEqual(r.status_code, 200, r.content)
        second = self.get("timer-schedule").json()["items"][0]
        self.assertGreater(second["generation"], first["generation"])
        self.assertNotEqual(second["due"], first["due"])
        token = self.get(path).json()["tokens"]["archive"]
        r = self.post(path + "/archive/active", {"token": token})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.get("timer-schedule").json()["items"], [])

    def test_local_reminder_preference_cannot_change_other_installation(self):
        device = MobileDevice.objects.create(user=self.other, installation_id=uuid.uuid4(),
            token='x'*40, platform='android', session_key='foreign')
        self.assertEqual(self.post('devices/reminder-mode', {'installation_id': str(device.installation_id),
            'local_posture_reminders': True}).status_code, 200)
        device.refresh_from_db()
        self.assertFalse(device.local_posture_reminders)
