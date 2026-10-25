import json

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from CuidadosApp.access import patient_for
from CuidadosApp.permissions import CareOwnerMixin

from . import consent, erase, export, forms
from .middleware import SESSION_KEY
from .models import PrivacyOperation


def download(data, filename):
    response = HttpResponse(
        json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Cache-Control"] = "no-store, private"
    return response


def stamp():
    return timezone.localdate().strftime("%Y%m%d")


class PolicyView(View):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        return render(
            request,
            "pages/PrivacidadApp/politica.html",
            {"version": consent.version()},
        )


class AcceptView(LoginRequiredMixin, View):
    def next_url(self, request):
        target = request.POST.get("next") or request.GET.get("next") or "/"
        ok = url_has_allowed_host_and_scheme(
            target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        )
        return target if ok else "/"

    def show(self, request, form):
        return render(
            request,
            "pages/PrivacidadApp/aceptar.html",
            {"form": form, "version": consent.version(), "next": self.next_url(request)},
        )

    def get(self, request):
        return self.show(request, forms.AcceptForm())

    def post(self, request):
        form = forms.AcceptForm(request.POST)
        if not form.is_valid():
            return self.show(request, form)
        consent.accept_account(request.user)
        request.session[SESSION_KEY] = consent.version()
        return redirect(self.next_url(request))


class ExportAccountView(LoginRequiredMixin, View):
    http_method_names = ["post", "options"]

    def post(self, request):
        data = export.account_data(request.user)
        PrivacyOperation.objects.create(kind="export_account")
        return download(data, f"vigia-cuenta-{stamp()}.json")


class DeleteAccountView(LoginRequiredMixin, View):
    def show(self, request, form):
        return render(
            request,
            "pages/PrivacidadApp/eliminar_cuenta.html",
            {"form": form, "has_password": request.user.has_usable_password()},
        )

    def get(self, request):
        return self.show(request, forms.DeleteAccountForm())

    def post(self, request):
        form = forms.DeleteAccountForm(request.POST)
        if form.is_valid():
            try:
                erase.erase_account(
                    request.user,
                    form.cleaned_data["password"],
                    form.cleaned_data["confirmation"],
                )
            except (ValidationError, DatabaseError) as error:
                form.add_error(
                    None,
                    error
                    if isinstance(error, ValidationError)
                    else "No se pudo eliminar. Ningún dato se borró; inténtalo nuevamente.",
                )
            else:
                logout(request)
                messages.success(request, "Tu cuenta y tus datos fueron eliminados.")
                return redirect("account_login")
        return self.show(request, form)


class PatientPrivacyView(CareOwnerMixin, View):
    """Base for titular-only actions on one patient (spec 014)."""

    action = "manage_access"

    def patient(self, request, pk):
        return patient_for(request.user, pk, self.action)[0]


class ConsentView(PatientPrivacyView):
    http_method_names = ["post", "options"]

    def post(self, request, pk):
        self.patient(request, pk)
        form = forms.PatientConsentForm(request.POST)
        try:
            if not form.is_valid():
                raise ValidationError(
                    [m for errors in form.errors.values() for m in errors]
                )
            data = form.cleaned_data
            consent.register(
                request.user,
                pk,
                data["scope"],
                data["consent_basis"],
                data["representative_name"],
                data["representative_relation"],
            )
        except (ValidationError, DatabaseError) as error:
            messages.error(
                request,
                error.messages[0]
                if isinstance(error, ValidationError)
                else "No se pudo registrar el consentimiento.",
            )
        else:
            messages.success(request, "Consentimiento registrado.")
        return redirect("CuidadosApp:patient", pk=pk)


class RevokeConsentView(PatientPrivacyView):
    http_method_names = ["post", "options"]

    def post(self, request, pk, scope):
        self.patient(request, pk)
        if scope not in consent.MISSING:
            return redirect("CuidadosApp:patient", pk=pk)
        consent.revoke(request.user, pk, scope)
        messages.success(
            request,
            "Consentimiento revocado. No se aceptarán datos nuevos de este tipo; "
            "los existentes se conservan hasta que los elimines o venzan.",
        )
        return redirect("CuidadosApp:patient", pk=pk)


class ExportPatientView(PatientPrivacyView):
    http_method_names = ["post", "options"]
    action = "export_patient"

    def post(self, request, pk):
        patient = self.patient(request, pk)
        data = export.patient_data(patient)
        PrivacyOperation.objects.create(kind="export_patient")
        return download(data, f"vigia-paciente-{patient.pk}-{stamp()}.json")


class DeletePatientView(PatientPrivacyView):
    action = "erase_patient"

    def show(self, request, patient, form):
        return render(
            request,
            "pages/PrivacidadApp/eliminar_paciente.html",
            {"patient": patient, "form": form},
        )

    def get(self, request, pk):
        return self.show(request, self.patient(request, pk), forms.DeletePatientForm())

    def post(self, request, pk):
        patient = self.patient(request, pk)
        form = forms.DeletePatientForm(request.POST)
        if form.is_valid():
            try:
                erase.delete_patient(request.user, pk, form.cleaned_data["typed_name"])
            except (ValidationError, DatabaseError) as error:
                form.add_error(
                    None,
                    error
                    if isinstance(error, ValidationError)
                    else "No se pudo eliminar. Ningún dato se borró.",
                )
            else:
                messages.success(request, "Paciente y todos sus datos eliminados.")
                return redirect("CuidadosApp:patients")
        return self.show(request, patient, form)
