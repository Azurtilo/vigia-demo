from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Position, Profile


@transaction.atomic
def provision_public_user(user):
    """Solo se llama durante el alta pública; nunca demueve perfiles existentes."""
    from PlanesApp.services import ensure_subscription

    position = Position.objects.get(user_position="Cliente público")
    if position.permission_code != "RESTRICTED":
        raise ValidationError("El cargo público no está configurado correctamente.")
    Profile.objects.get_or_create(user_FK=user, defaults={"position_FK": position})
    ensure_subscription(user)
