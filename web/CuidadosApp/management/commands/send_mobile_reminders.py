"""Run periodically in deployment; never claim delivery without FCM success."""

from datetime import timedelta

from allauth.headless.internal.sessionkit import authenticate_by_x_session_token
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from CuidadosApp import push
from CuidadosApp.access import risk_patient_ids
from CuidadosApp.models import MobileDevice, PostureObservation, PushReceipt
from CuidadosApp.scheduling import reminders
from PlanesApp.services import locked_user

# Lock-screen text never names the patient or the event (D-058). Falls go first
# and with high priority. A risk stays pending until FCM accepts it (one
# confirmed PushReceipt per device), so a late delivery, an FCM failure or a
# lost immediate push (D-051) is retried on the next run instead of lost.
RISK_PUSH_MAX_AGE = timedelta(hours=1)
RISK_MESSAGES = {"fall": push.RISK_TEXT, "immobility": push.RISK_TEXT}
CARE_TEXT = "Tienes un cuidado pendiente. Abre VIGIA para revisarlo."


class Command(BaseCommand):
    help = "Send generic mobile reminders using configured Firebase credentials."

    def handle(self, *args, **options):
        if not getattr(settings, "VIGIA_PUSH_ENABLED", False):
            raise CommandError(
                "VIGIA_PUSH_ENABLED está desactivado; no se enviaron notificaciones."
            )
        fcm = push.firebase()
        if fcm is None:
            raise CommandError("Instala requirements-push.txt en el entorno de envío.")
        sent = 0
        for device_id in MobileDevice.objects.filter(active=True).values_list(
            "pk", flat=True
        ):
            # Short locked section: validate the session and pick candidates only.
            with transaction.atomic():
                device = MobileDevice.objects.select_related("user").get(pk=device_id)
                user = locked_user(device.user)
                auth = authenticate_by_x_session_token(device.session_key)
                if not auth or auth[0].pk != user.pk or not user.is_active:
                    device.active, device.token = False, ""
                    device.save(update_fields=["active", "token"])
                    continue
                candidates = self.candidates(device, user)
            # QA-2026-10-22-09: FCM is called outside any transaction.
            for key, body, risk in candidates:
                try:
                    sent += push.deliver(fcm, device, key, body, risk)
                except (fcm[1], ValueError) as exc:
                    self.stderr.write(f"Entrega no confirmada: {type(exc).__name__}")
        self.stdout.write(
            f"Notificaciones aceptadas por FCM: {sent}. La recepción requiere verificación en dispositivo."
        )

    def candidates(self, device, user):
        care = [
            (r["key"], CARE_TEXT, None)
            for r in reminders(user)
            if not r["seen"]
            and not (device.local_posture_reminders and r["key"].startswith("posture:"))
        ]
        # Spec 013: titular, family and caregivers (D-063), titular's plan.
        ids = risk_patient_ids(user)
        risks = []
        if ids:
            rows = PostureObservation.objects.filter(
                node__patient_id__in=ids,
                node__active=True,
                risk__in=RISK_MESSAGES,
                received_at__gte=timezone.now() - RISK_PUSH_MAX_AGE,
            )
            risks = [
                (f"edge:{r.pk}", RISK_MESSAGES[r.risk], r.risk)
                for r in sorted(rows, key=lambda r: (r.risk != "fall", r.received_at))
            ]
        done = set(
            PushReceipt.objects.filter(device=device, confirmed=True).values_list(
                "key", flat=True
            )
        )
        return [c for c in risks + care if c[0] not in done]
