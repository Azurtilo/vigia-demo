import re

from django import forms
from django.utils import timezone

from .models import CareGuide, CareTask, Medication, Patient


class PatientForm(forms.ModelForm):
    version = forms.IntegerField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Patient
        fields = [
            "name",
            "birth_date",
            "notes",
            "contact_name",
            "contact_phone",
            "contact_relation",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_birth_date(self):
        date = self.cleaned_data.get("birth_date")
        if date and date > timezone.localdate():
            raise forms.ValidationError("La fecha de nacimiento no puede ser futura.")
        return date

    def clean(self):
        data = super().clean()
        contact = [
            data.get(k) for k in ("contact_name", "contact_phone", "contact_relation")
        ]
        if any(contact) and not all(contact):
            raise forms.ValidationError(
                "Completa nombre, teléfono y relación del contacto de emergencia."
            )
        phone = data.get("contact_phone", "")
        if phone and (
            not re.fullmatch(r"[+\d ()-]{6,30}", phone)
            or sum(c.isdigit() for c in phone) < 6
        ):
            self.add_error(
                "contact_phone", "Escribe un teléfono con al menos seis dígitos."
            )
        return data


class DailyForm(forms.ModelForm):
    version = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def clean(self):
        data = super().clean()
        if (
            data.get("start_date")
            and data.get("end_date")
            and data["end_date"] < data["start_date"]
        ):
            self.add_error(
                "end_date", "El término debe ser igual o posterior al inicio."
            )
        return data


class MedicationForm(DailyForm):
    hours = forms.CharField(
        label="Horarios diarios",
        help_text="Formato 08:00, 14:00, 20:00; sin duplicados.",
        max_length=160,
    )

    class Meta:
        model = Medication
        fields = ["name", "dose", "notes", "hours", "start_date", "end_date", "active"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "end_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["hours"] = ", ".join(
                t.time.strftime("%H:%M") for t in self.instance.times.all()
            )

    def clean_hours(self):
        from datetime import time

        entries = [s.strip() for s in self.cleaned_data["hours"].split(",")]
        if (
            not entries
            or len(entries) > 12
            or any(not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", s) for s in entries)
        ):
            raise forms.ValidationError(
                "Usa entre uno y doce horarios válidos HH:MM separados por coma."
            )
        if len(set(entries)) != len(entries):
            raise forms.ValidationError("No repitas el mismo horario.")
        return [time.fromisoformat(s) for s in entries]


class TaskForm(DailyForm):
    class Meta:
        model = CareTask
        fields = ["name", "notes", "time", "start_date", "end_date", "active"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "end_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class SignedForm(forms.Form):
    token = forms.CharField(widget=forms.HiddenInput)


class PostureForm(SignedForm):
    guide = forms.ModelChoiceField(
        label="Postura realizada",
        queryset=CareGuide.objects.filter(active=True, category="posture"),
        empty_label="Selecciona la postura",
    )
    interval = forms.TypedChoiceField(
        label="Próximo cambio",
        coerce=int,
        choices=[(60, "En 1 hora"), (90, "En 90 minutos"), (120, "En 2 horas")],
        initial=120,
    )
    note = forms.CharField(
        label="Nota (opcional)",
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class TimerForm(SignedForm):
    action = forms.ChoiceField(
        label="Acción",
        choices=[
            ("start", "Crear recordatorio"),
            ("interval", "Cambiar intervalo"),
            ("pause", "Pausar recordatorios"),
            ("resume", "Reanudar recordatorios"),
        ],
    )
    interval = forms.TypedChoiceField(
        label="Intervalo",
        coerce=int,
        choices=[(60, "1 hora"), (90, "90 minutos"), (120, "2 horas")],
    )


class EventForm(SignedForm):
    status = forms.ChoiceField(
        label="Resultado", choices=[("done", "Realizado"), ("omitted", "Omitido")]
    )
    note = forms.CharField(
        label="Nota / motivo",
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean(self):
        data = super().clean()
        if data.get("status") == "omitted" and not data.get("note"):
            self.add_error("note", "Indica el motivo de la omisión.")
        return data


class CorrectionForm(SignedForm):
    note = forms.CharField(
        label="Corrección del registro",
        min_length=2,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 4}),
    )


class SelectionForm(SignedForm):
    patients = forms.ModelMultipleChoiceField(
        label="Pacientes que seguirán activos",
        queryset=Patient.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patients"].queryset = Patient.objects.filter(
            owner=user, active=True
        )
        self.fields["patients"].label_from_instance = lambda patient: patient.name
