"""Spec 012 adjustments: immediate fall push (D-051), receipts outside locks (QA-09)."""

import hashlib
import json
import sys
import types
import uuid
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.db import connection
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from PlanesApp.models import Plan, Subscription

from . import push
from .models import DetectionNode, MobileDevice, Patient, PushReceipt

PASSWORD = "Demo-strong-123!"
NODE_TOKEN = "nodo-de-prueba-" + "x" * 30


class FakeFirebase:
    """Collects messages; the first `failures` sends raise FirebaseError."""

    class FirebaseError(Exception):
        pass

    def __init__(self, failures=0, check=None):
        self.sent, self.failures, self.check = [], failures, check
        self.messaging = types.SimpleNamespace(
            Message=lambda **kw: kw,
            Notification=lambda **kw: kw,
            AndroidConfig=lambda **kw: kw,
            AndroidNotification=lambda **kw: kw,
            send=self.send,
        )

    def send(self, message):
        if self.check:
            self.check()
        if self.failures:
            self.failures -= 1
            raise self.FirebaseError("no disponible")
        self.sent.append(message)

    def modules(self):
        return {
            "firebase_admin": types.SimpleNamespace(
                _apps=[object()], messaging=self.messaging
            ),
            "firebase_admin.messaging": self.messaging,
            "firebase_admin.exceptions": types.SimpleNamespace(
                FirebaseError=self.FirebaseError
            ),
        }

    @property
    def fcm(self):
        return self.messaging, self.FirebaseError


@override_settings(VIGIA_PUSH_ENABLED=True, VIGIA_PUSH_INLINE=True)
class ImmediateFallPushTests(TestCase):
    def setUp(self):
        cache.clear()
        self.titular = User.objects.create_user("titular", "t@example.test", PASSWORD)
        plan = Plan.objects.get(code="pro")
        Subscription.objects.create(
            user=self.titular,
            plan=plan,
            plan_name=plan.name,
            amount_clp=plan.amount_clp,
            start=timezone.now() - timedelta(days=1),
            end=timezone.now() + timedelta(days=29),
        )
        self.patient = Patient.objects.create(owner=self.titular, name="Paciente demo")
        DetectionNode.objects.create(
            patient=self.patient,
            name="Cámara",
            credential_hash=hashlib.sha256(NODE_TOKEN.encode()).hexdigest(),
        )
        token = Client().post(
            "/_allauth/app/v1/auth/login",
            data=json.dumps({"username": "titular", "password": PASSWORD}),
            content_type="application/json",
        ).json()["meta"]["session_token"]
        Client().post(
            "/api/v1/devices",
            data=json.dumps(
                {
                    "installation_id": str(uuid.uuid4()),
                    "token": "device-token-not-real-titular",
                    "platform": "android",
                    "enabled": True,
                }
            ),
            content_type="application/json",
            HTTP_X_SESSION_TOKEN=token,
        )

    def observe(self, firebase, risk="fall", posture="indeterminada"):
        data = {
            "event_id": str(uuid.uuid4()),
            "observed_at": timezone.now().isoformat(),
            "posture": posture,
            "confidence": 0.0 if posture == "indeterminada" else 0.8,
            "model_version": "test",
            "rule_version": "fall-v1",
            "risk": risk,
        }
        with patch.dict(sys.modules, firebase.modules()):
            with self.captureOnCommitCallbacks(execute=True):
                return Client().post(
                    "/api/v1/edge/observations",
                    data=json.dumps(data),
                    content_type="application/json",
                    HTTP_AUTHORIZATION="Bearer " + NODE_TOKEN,
                )

    def run_command(self, firebase):
        with patch.dict(sys.modules, firebase.modules()):
            call_command("send_mobile_reminders", stdout=StringIO(), stderr=StringIO())

    def test_fall_is_pushed_on_reception_and_not_repeated(self):
        firebase = FakeFirebase()
        self.assertEqual(self.observe(firebase).status_code, 201)
        [message] = firebase.sent
        self.assertEqual(message["notification"]["body"], push.RISK_TEXT)
        self.assertEqual(
            message["android"],
            {"priority": "high", "notification": {"visibility": "private"}},
        )
        self.run_command(firebase)
        self.assertEqual(len(firebase.sent), 1)
        self.assertTrue(PushReceipt.objects.get().confirmed)

    def test_immobility_waits_for_the_command(self):
        firebase = FakeFirebase()
        response = self.observe(firebase, risk="immobility", posture="supina")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(firebase.sent, [])
        self.run_command(firebase)
        self.assertEqual(len(firebase.sent), 1)

    def test_fcm_failure_keeps_node_response_and_command_retries(self):
        firebase = FakeFirebase(failures=1)
        self.assertEqual(self.observe(firebase).status_code, 201)
        self.assertEqual(firebase.sent, [])
        self.assertFalse(PushReceipt.objects.exists())
        self.run_command(firebase)
        self.run_command(firebase)
        self.assertEqual(len(firebase.sent), 1)


@override_settings(VIGIA_PUSH_ENABLED=True, VIGIA_PUSH_INLINE=True)
class NodeAlertTests(TestCase):
    """Spec 017 (D-074, D-075): blind camera and silent node, once per episode."""

    setUp = ImmediateFallPushTests.setUp
    observe = ImmediateFallPushTests.observe
    run_command = ImmediateFallPushTests.run_command

    def node(self, **fields):
        DetectionNode.objects.update(**fields)

    def monitor_messages(self, firebase):
        return [m for m in firebase.sent if m["notification"]["body"] == push.MONITOR_TEXT]

    def test_blind_states_alert_once_per_episode_without_high_priority(self):
        firebase, now = FakeFirebase(), timezone.now()
        self.node(last_seen_at=now, monitor_state="persona_no_visible", monitor_since=now)
        self.run_command(firebase)
        self.run_command(firebase)
        [message] = self.monitor_messages(firebase)
        self.assertEqual(
            message["android"], {"priority": None, "notification": {"visibility": "private"}}
        )
        self.assertNotIn("Paciente", message["notification"]["body"])
        self.node(monitor_state="normal", monitor_since=now + timedelta(seconds=5))
        self.run_command(firebase)
        # Same state again after "normal": a new episode, a new alert.
        self.node(monitor_state="persona_no_visible", monitor_since=now + timedelta(seconds=9))
        self.run_command(firebase)
        self.run_command(firebase)
        self.assertEqual(len(self.monitor_messages(firebase)), 2)
        self.node(monitor_state="sin_imagen", monitor_since=now + timedelta(seconds=12))
        self.run_command(firebase)
        self.assertEqual(len(self.monitor_messages(firebase)), 3)

    def test_low_light_and_unknown_state_are_not_pushed(self):
        firebase, now = FakeFirebase(), timezone.now()
        for state in ("poca_luz", "normal", ""):
            with self.subTest(state):
                self.node(last_seen_at=now, monitor_state=state, monitor_since=now)
                self.run_command(firebase)
        self.assertEqual(firebase.sent, [])

    def test_silent_node_alerts_once_and_again_after_reconnecting(self):
        firebase, now = FakeFirebase(), timezone.now()
        self.node(last_seen_at=now - timedelta(seconds=50), monitor_state="normal")
        self.run_command(firebase)
        self.assertEqual(firebase.sent, [])  # still within 60 s
        self.node(last_seen_at=now - timedelta(seconds=61))
        self.run_command(firebase)
        self.run_command(firebase)
        self.assertEqual(len(self.monitor_messages(firebase)), 1)
        self.node(last_seen_at=now)  # renewed: the episode is over
        self.run_command(firebase)
        self.node(last_seen_at=now - timedelta(seconds=70))
        self.run_command(firebase)
        self.assertEqual(len(self.monitor_messages(firebase)), 2)

    def test_old_episodes_are_not_announced(self):
        firebase, old = FakeFirebase(), timezone.now() - timedelta(hours=2)
        self.node(last_seen_at=timezone.now(), monitor_state="sin_imagen", monitor_since=old)
        self.run_command(firebase)
        self.node(last_seen_at=old, monitor_state="normal")
        self.run_command(firebase)
        self.assertEqual(firebase.sent, [])

    def test_stopped_on_purpose_or_without_risk_alerts_is_silent(self):
        firebase, now = FakeFirebase(), timezone.now()
        silent = {"last_seen_at": now - timedelta(seconds=90), "monitor_state": "normal"}
        self.node(**silent, active=False)
        self.run_command(firebase)
        self.node(active=True)
        Patient.objects.update(active=False)  # archived: outside the capacity
        self.run_command(firebase)
        Patient.objects.update(active=True)
        with self.settings(PRIVACY_ENFORCED=True):  # no detection consent recorded
            self.run_command(firebase)
        Subscription.objects.update(end=now - timedelta(seconds=1))  # plan without risk_alerts
        self.node(monitor_state="sin_imagen", monitor_since=now, last_seen_at=now)
        self.run_command(firebase)
        self.assertEqual(firebase.sent, [])

    def test_falls_go_before_node_alerts(self):
        firebase, now = FakeFirebase(), timezone.now()
        with patch.object(push, "schedule_fall"):  # leave the fall to the command
            self.assertEqual(self.observe(firebase).status_code, 201)
        self.node(last_seen_at=now, monitor_state="sin_imagen", monitor_since=now)
        self.run_command(firebase)
        bodies = [m["notification"]["body"] for m in firebase.sent]
        self.assertEqual(bodies, [push.RISK_TEXT, push.MONITOR_TEXT])


class ReservationTests(TransactionTestCase):
    """Real transactions: TestCase would hide whether FCM runs inside one."""

    def setUp(self):
        user = User.objects.create_user("dispositivo", "d@example.test", PASSWORD)
        self.device = MobileDevice.objects.create(
            user=user,
            installation_id=uuid.uuid4(),
            token="device-token-not-real",
            platform="android",
            session_key="x",
        )

    def test_fcm_is_called_outside_any_transaction(self):
        firebase = FakeFirebase(
            check=lambda: self.assertFalse(connection.in_atomic_block)
        )
        self.assertTrue(push.deliver(firebase.fcm, self.device, "edge:1", "texto", "fall"))
        self.assertFalse(push.deliver(firebase.fcm, self.device, "edge:1", "texto", "fall"))
        self.assertEqual(len(firebase.sent), 1)

    def test_failure_releases_and_stale_reservations_expire(self):
        firebase = FakeFirebase(failures=1)
        with self.assertRaises(FakeFirebase.FirebaseError):
            push.deliver(firebase.fcm, self.device, "edge:2", "texto")
        self.assertFalse(PushReceipt.objects.exists())
        # A reservation left by a crashed process blocks only for two minutes.
        stale = PushReceipt.objects.create(device=self.device, key="edge:3", confirmed=False)
        self.assertFalse(push.deliver(firebase.fcm, self.device, "edge:3", "texto"))
        PushReceipt.objects.filter(pk=stale.pk).update(
            sent_at=timezone.now() - timedelta(minutes=3)
        )
        self.assertTrue(push.deliver(firebase.fcm, self.device, "edge:3", "texto"))


class DemoSafetyTests(TestCase):
    """QA-2026-10-22-10: the DEBUG demo never uses a versioned key or public hosts."""

    def test_only_loopback_or_private_hosts(self):
        from django.core.exceptions import ImproperlyConfigured

        from core.demo_safety import private_hosts

        self.assertEqual(
            private_hosts("192.168.1.20, 10.0.0.5,127.0.0.1"),
            ["192.168.1.20", "10.0.0.5", "127.0.0.1"],
        )
        self.assertEqual(private_hosts(""), [])
        for bad in ("8.8.8.8", "demo.example.com", "0.0.0.0", "192.168.1.2,1.1.1.1"):
            with self.subTest(hosts=bad), self.assertRaises(ImproperlyConfigured):
                private_hosts(bad)

    def test_secret_key_is_random_and_stable(self):
        import tempfile
        from pathlib import Path

        from core.demo_safety import demo_secret_key

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "secret_key"
            first = demo_secret_key(path)
            self.assertGreaterEqual(len(first), 50)
            self.assertEqual(demo_secret_key(path), first)
        with tempfile.TemporaryDirectory() as folder:
            self.assertNotEqual(demo_secret_key(Path(folder) / "secret_key"), first)
