import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse

from CuidadosApp.models import MobileDevice
from PlanesApp.services import locked_user

from .base import MobileView


class DevicesView(MobileView):
    @transaction.atomic
    def post(self, request):
        user = locked_user(request.user)
        installation = uuid.UUID(self.data["installation_id"])
        enabled = self.data.get("enabled") is True
        if not enabled:
            MobileDevice.objects.filter(user=user, installation_id=installation).update(
                active=False, token=""
            )
            return JsonResponse({"enabled": False})
        token, platform = self.data.get("token", ""), self.data.get("platform")
        if (
            not isinstance(token, str)
            or not 20 <= len(token) <= 4096
            or platform not in ("ios", "android")
        ):
            raise ValidationError("Dispositivo o permiso inválidos.")
        # Client installation identifiers are random, not claims to clinical data.
        existing = MobileDevice.objects.filter(installation_id=installation).first()
        if existing and existing.user_id != user.pk:
            raise ValidationError("Registra una nueva instalación para esta cuenta.")
        MobileDevice.objects.update_or_create(
            installation_id=installation,
            defaults={
                "user": user,
                "token": token,
                "platform": platform,
                "active": True,
                "local_posture_reminders": self.data.get("local_posture_reminders") is True,
                "session_key": request.headers["X-Session-Token"],
            },
        )
        return JsonResponse(
            {
                "enabled": True,
                "delivery_configured": getattr(settings, "VIGIA_PUSH_ENABLED", False),
            }
        )


class ReminderModeView(MobileView):
    def post(self, request):
        installation = uuid.UUID(self.data["installation_id"])
        MobileDevice.objects.filter(user=request.user, installation_id=installation).update(
            local_posture_reminders=self.data.get("local_posture_reminders") is True)
        return JsonResponse({"saved": True})
