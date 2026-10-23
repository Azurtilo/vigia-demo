"""Run periodically in deployment; never claim delivery without FCM success."""

from datetime import timedelta

from allauth.headless.internal.sessionkit import authenticate_by_x_session_token
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from CuidadosApp.capacity import capacity_state
from CuidadosApp.models import MobileDevice, PostureObservation, PushReceipt
from CuidadosApp.scheduling import reminders
from PlanesApp.entitlements import capabilities
from PlanesApp.services import locked_user


class Command(BaseCommand):
    help = "Send generic mobile reminders using configured Firebase credentials."

    def handle(self, *args, **options):
        if not getattr(settings, "VIGIA_PUSH_ENABLED", False):
            raise CommandError(
                "VIGIA_PUSH_ENABLED está desactivado; no se enviaron notificaciones."
            )
        try:
            import firebase_admin
            from firebase_admin import messaging
            from firebase_admin.exceptions import FirebaseError
        except ImportError as exc:
            raise CommandError(
                "Instala requirements-push.txt en el entorno de envío."
            ) from exc
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        sent = 0
        for device_id in MobileDevice.objects.filter(active=True).values_list(
            "pk", flat=True
        ):
            with transaction.atomic():
                device = MobileDevice.objects.select_related("user").get(pk=device_id)
                user = locked_user(device.user)
                auth = authenticate_by_x_session_token(device.session_key)
                if not auth or auth[0].pk != user.pk or not user.is_active:
                    device.active, device.token = False, ""
                    device.save(update_fields=["active", "token"])
                    continue
                candidates = [
                    (
                        r["key"],
                        "Tienes un cuidado pendiente. Abre VIGIA para revisarlo.",
                    )
                    for r in reminders(user)
                    if not r["seen"] and not (device.local_posture_reminders and r["key"].startswith("posture:"))
                ]
                if capabilities(user)["features"]["risk_alerts"]:
                    ids = capacity_state(user)["active_ids"]
                    rows = PostureObservation.objects.filter(
                        node__patient_id__in=ids,
                        node__active=True,
                        risk="immobility",
                        observed_at__gte=timezone.now() - timedelta(minutes=2),
                    )
                    candidates += [
                        (f"edge:{r.pk}", "Revisa un aviso de monitoreo en VIGIA.")
                        for r in rows
                    ]
                for key, body in candidates:
                    if PushReceipt.objects.filter(device=device, key=key).exists():
                        continue
                    try:
                        messaging.send(
                            messaging.Message(
                                token=device.token,
                                notification=messaging.Notification(
                                    title="VIGIA", body=body
                                ),
                            )
                        )
                    except (FirebaseError, ValueError) as exc:
                        self.stderr.write(
                            f"Entrega no confirmada: {type(exc).__name__}"
                        )
                        continue
                    PushReceipt.objects.create(device=device, key=key)
                    sent += 1
        self.stdout.write(
            f"Notificaciones aceptadas por FCM: {sent}. La recepción requiere verificación en dispositivo."
        )
