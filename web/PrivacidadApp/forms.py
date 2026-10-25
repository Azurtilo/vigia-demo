from django import forms

from .models import PatientConsent


class AcceptForm(forms.Form):
    accept = forms.BooleanField(
        label="Leí y acepto la política de privacidad de VIGIA",
        error_messages={"required": "Debes aceptar la política para continuar."},
    )


class ConsentFieldsMixin(forms.Form):
    """Who consents for the patient; shared by patient creation and the consent form."""

    consent_basis = forms.ChoiceField(
        label="¿Quién da el consentimiento?", choices=PatientConsent.BASES
    )
    representative_name = forms.CharField(
        label="Nombre del representante", max_length=120, required=False
    )
    representative_relation = forms.CharField(
        label="Relación con el paciente", max_length=60, required=False
    )
    consent_confirm = forms.BooleanField(
        label="Confirmo que cuento con ese consentimiento para tratar estos datos de salud",
        error_messages={"required": "Confirma el consentimiento para continuar."},
    )

    def clean(self):
        data = super().clean()
        if data.get("consent_basis") == "representante":
            # Next to each field, where the person is looking (a form-level
            # error renders at the top, far from these inputs).
            for field, message in (
                ("representative_name", "Indica el nombre del representante."),
                ("representative_relation", "Indica la relación con el paciente."),
            ):
                if not (data.get(field) or "").strip():
                    self.add_error(field, message)
        return data


class PatientConsentForm(ConsentFieldsMixin):
    scope = forms.ChoiceField(label="Alcance", choices=PatientConsent.SCOPES)


class DeletePatientForm(forms.Form):
    typed_name = forms.CharField(
        label="Escribe el nombre del paciente para confirmar", max_length=120
    )


class DeleteAccountForm(forms.Form):
    password = forms.CharField(
        label="Tu contraseña", widget=forms.PasswordInput, required=False
    )
    confirmation = forms.CharField(
        label="Si entraste con Google, escribe tu nombre de usuario",
        required=False,
    )
