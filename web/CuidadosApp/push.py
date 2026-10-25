"""FCM delivery shared by the periodic command and the immediate fall push (spec 012).

Never called inside a transaction that holds row locks (QA-2026-10-22-09): a
receipt is reserved in a short transaction, FCM is called outside it, and the
receipt is then confirmed or released. The (device, key) unique constraint
stops the command and the immediate push from sending the same alert twice.
"""

import logging
import threading
from datetime import timedelta

from allauth.headless.internal.sessionkit import authenticate_by_x_session_token
from django.conf import settings
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from .models import MobileDevice, PostureObservation, PushReceipt

log = logging.getLogger("vigia.push")

# D-058: one generic text; the lock screen never reveals a health event.
RISK_TEXT = "VIGIA: alerta de riesgo, abre la app."
RESERVATION_TTL = timedelta(minutes=2)


def firebase():
    """(messaging, FirebaseError), or None when push is off or not installed."""
    if not getattr(settings, "VIGIA_PUSH_ENABLED", False):
        return None
    try:
        import firebase_admin
        from firebase_admin import messaging
        from firebase_admin.exceptions import FirebaseError
    except ImportError:
        return None
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    return messaging, FirebaseError


def build(messaging, token, body, risk=None):
    android = None
    if risk:
        android = messaging.AndroidConfig(
            priority="high" if risk == "fall" else None,
            notification=messaging.AndroidNotification(visibility="private"),
        )
    return messaging.Message(
        token=token,
        notification=messaging.Notification(title="VIGIA", body=body),
        android=android,
    )


def deliver(fcm, device, key, body, risk=None):
    """True if FCM accepted it now; False if already sent or in flight.

    Raises the FCM error after releasing the reservation, so a later run retries.
    """
    messaging, firebase_error = fcm
    with transaction.atomic():
        PushReceipt.objects.filter(
            device=device,
            confirmed=False,
            sent_at__lt=timezone.now() - RESERVATION_TTL,
        ).delete()
        try:
            with transaction.atomic():
                receipt = PushReceipt.objects.create(
                    device=device, key=key, confirmed=False
                )
        except IntegrityError:
            return False
    try:
        messaging.send(build(messaging, device.token, body, risk))
    except (firebase_error, ValueError):
        PushReceipt.objects.filter(pk=receipt.pk, confirmed=False).delete()
        raise
    PushReceipt.objects.filter(pk=receipt.pk).update(
        confirmed=True, sent_at=timezone.now()
    )
    return True


def send_fall(observation_id):
    """Immediate fall push to every device of the patient's recipients (D-051, D-063)."""
    from PlanesApp.entitlements import capabilities

    from .access import recipients
    from .capacity import capacity_state

    fcm = firebase()
    if fcm is None:
        return
    observation = PostureObservation.objects.select_related(
        "node__patient__owner"
    ).get(pk=observation_id)
    patient = observation.node.patient
    titular = patient.owner
    if not (
        observation.risk == "fall"
        and observation.node.active
        and capabilities(titular)["features"]["risk_alerts"]
        and patient.pk in capacity_state(titular)["active_ids"]
    ):
        return
    for device in MobileDevice.objects.filter(
        user_id__in=recipients(patient, "risk"), active=True, user__is_active=True
    ):
        auth = authenticate_by_x_session_token(device.session_key)
        if not auth or auth[0].pk != device.user_id:
            continue  # the periodic command deactivates stale devices
        try:
            deliver(fcm, device, f"edge:{observation.pk}", RISK_TEXT, "fall")
        except Exception as exc:  # retried by send_mobile_reminders
            log.warning("Push inmediato no confirmado: %s", type(exc).__name__)


def schedule_fall(observation_id):
    """Runs after commit; a daemon thread keeps the node's response off FCM."""
    if not getattr(settings, "VIGIA_PUSH_ENABLED", False):
        return
    if getattr(settings, "VIGIA_PUSH_INLINE", False):
        send_fall(observation_id)
        return

    def run():
        try:
            send_fall(observation_id)
        except Exception as exc:
            log.warning("Push inmediato falló: %s", type(exc).__name__)
        finally:
            connection.close()

    threading.Thread(target=run, daemon=True).start()
