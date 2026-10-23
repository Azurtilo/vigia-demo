import re

from django import forms
from django.views.decorators.debug import sensitive_variables

from .simulator import card_fixture, expired


class EmptySensitiveInput(forms.TextInput):
    def format_value(self, value):
        return ""


class PaymentMethodForm(forms.Form):
    holder = forms.CharField(
        label="Nombre en la tarjeta",
        min_length=2,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "placeholder": "Ana Demo",
                "data-card-holder": "",
            }
        ),
    )
    number = forms.CharField(
        label="Número de prueba",
        max_length=24,
        widget=EmptySensitiveInput(
            attrs={
                "autocomplete": "off",
                "inputmode": "numeric",
                "placeholder": "4242 4242 4242 4242",
                "data-card-number": "",
            }
        ),
    )
    expiry = forms.CharField(
        label="Vencimiento (MM/AA)",
        max_length=5,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "inputmode": "numeric",
                "placeholder": "12/30",
                "data-card-expiry": "",
            }
        ),
    )
    cvc = forms.CharField(
        label="CVC de prueba",
        max_length=3,
        widget=EmptySensitiveInput(
            attrs={
                "autocomplete": "off",
                "inputmode": "numeric",
                "placeholder": "123",
                "data-card-cvc": "",
            }
        ),
    )

    def clean_holder(self):
        name = self.cleaned_data["holder"]
        if not any(c.isalpha() for c in name) or any(
            not (c.isalpha() or c in " '-.’") for c in name
        ):
            raise forms.ValidationError(
                "Escribe un nombre con letras, espacios o signos habituales, sin números."
            )
        return name

    @sensitive_variables()
    def clean(self):
        cleaned = super().clean()
        if "number" in cleaned:
            try:
                cleaned["fixture"] = card_fixture(cleaned["number"])
            except forms.ValidationError as error:
                self.add_error("number", error)
        value = cleaned.get("expiry", "")
        if re.fullmatch(r"(0[1-9]|1[0-2])/[0-9]{2}", value):
            month, year = int(value[:2]), 2000 + int(value[3:])
            if expired(month, year):
                self.add_error(
                    "expiry", "La fecha está vencida. Usa un mes vigente o futuro."
                )
            cleaned.update(month=month, year=year)
        elif value:
            self.add_error("expiry", "Usa MM/AA con un mes entre 01 y 12.")
        if "cvc" in cleaned and not re.fullmatch(r"[0-9]{3}", cleaned["cvc"]):
            self.add_error("cvc", "Usa tres dígitos de prueba, por ejemplo 123.")
        cleaned.pop("number", None)
        cleaned.pop("cvc", None)
        return cleaned


class ConfirmationForm(forms.Form):
    token = forms.CharField(widget=forms.HiddenInput)
    patients = forms.ModelMultipleChoiceField(
        label="Pacientes que seguirán activos",
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, user=None, target_limit=None, **kwargs):
        from CuidadosApp.models import Patient

        super().__init__(*args, **kwargs)
        self.fields["patients"].queryset = (
            Patient.objects.filter(owner=user, active=True)
            if user
            else Patient.objects.none()
        )
        self.fields["patients"].label_from_instance = lambda patient: patient.name
        count = self.fields["patients"].queryset.count()
        self.selection_limit = target_limit
        self.needs_selection = target_limit is not None and count > target_limit
        if not self.needs_selection:
            self.fields["patients"].widget = forms.MultipleHiddenInput()
        else:
            self.fields[
                "patients"
            ].help_text = f"Elige {target_limit}. Los restantes se archivarán conservando ficha e historial; dejarán de generar avisos."


class CheckoutForm(ConfirmationForm):
    method = forms.ModelChoiceField(
        label="Método de prueba",
        queryset=None,
        required=False,
        empty_label="Elige una tarjeta de prueba",
    )

    def __init__(self, *args, user, paid, target_limit=None, **kwargs):
        from .models import SimulatedPaymentMethod

        super().__init__(*args, user=user, target_limit=target_limit, **kwargs)
        self.fields["method"].queryset = SimulatedPaymentMethod.objects.filter(
            user=user, active=True
        )
        self.fields["method"].required = paid
        if not paid:
            self.fields["method"].widget = forms.HiddenInput()
