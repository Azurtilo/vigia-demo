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


class ReservationTests(TransactionTestCase):
    """Real transactions: TestCase would hide whether FCM runs inside one."""

    serialized_rollback = True

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
