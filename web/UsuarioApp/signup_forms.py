from allauth.account.forms import SignupForm
from django import forms
from django.db import transaction
from django.urls import reverse_lazy
from django.utils.functional import lazy
from django.utils.html import format_html

from PrivacidadApp.consent import accept_account

policy_label = lazy(
    lambda: format_html(
        'Leí y acepto la <a class="text-link" href="{}" target="_blank" rel="noopener">política de privacidad</a>',
        reverse_lazy("PrivacidadApp:policy"),
    ),
    str,
)


class PublicSignupForm(SignupForm):
    accept_privacy = forms.BooleanField(
        label=policy_label(),
        error_messages={"required": "Debes aceptar la política de privacidad."},
    )

    @transaction.atomic
    def save(self, request):
        # Wrap allauth's EmailAddress and custom_signup too, not only User.save.
        user = super().save(request)
        accept_account(user)
        return user
