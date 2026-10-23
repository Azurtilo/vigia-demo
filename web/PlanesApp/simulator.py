"""Escenarios locales: nunca contacta una pasarela ni acepta tarjetas reales."""

import re

from django.core.exceptions import ValidationError
from django.utils import timezone

CARDS = {
    "4242424242424242": ("visa_ok", "Visa", "4242"),
    "5555555555554444": ("mastercard_ok", "Mastercard", "4444"),
    "4000000000000002": ("declined", "Visa", "0002"),
    "4000000000009995": ("insufficient", "Visa", "9995"),
}
ERRORS = {
    "declined": "La tarjeta de prueba simula un rechazo. Elige otra tarjeta y vuelve a intentar.",
    "insufficient": "La tarjeta de prueba simula fondos insuficientes. Elige otro método.",
}


def card_fixture(number):
    normalized = re.sub(r"[ -]", "", number)
    if normalized not in CARDS:
        raise ValidationError(
            "Usa uno de los cuatro números de prueba indicados. No ingreses una tarjeta real."
        )
    return CARDS[normalized]


def expired(month, year, now=None):
    today = timezone.localtime(now or timezone.now())
    return (year, month) < (today.year, today.month)
