from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from PlanesApp.models import Subscription

from . import access, forms, invitations, services
from .capacity import capacity_state, choose_capacity, fingerprint
from .models import (
    CareEvent,
    CareGuide,
    CareTask,
    Medication,
    Patient,
    PatientAccess,
    PatientInvitation,
    PostureTimer,
)
from .permissions import CareOwnerMixin
from .scheduling import agenda, claim_reminder, reminders


def privacy_context(patient, can):
    """Consent status per scope for the titular's patient page (spec 014)."""
    if "manage_access" not in can:
        return {}
    from PrivacidadApp.models import PatientConsent

    live = {
        c.scope: c for c in patient.consents.filter(revoked_at__isnull=True)
    }
    consents = [
        {"scope": scope, "label": label, "consent": live.get(scope)}
        for scope, label in PatientConsent.SCOPES
    ]
    return {
        "consents": consents,
        "missing_consent": any(item["consent"] is None for item in consents),
    }


def form_error(form, error):
    form.add_error(
        None,
        error
        if isinstance(error, ValidationError)
        else "No se pudo guardar. Ningún cambio se confirmó; inténtalo nuevamente.",
    )


@method_decorator(never_cache, name="dispatch")
class CareView(CareOwnerMixin, View):
    # Spec 013: each view states the action it needs on the patient in its URL.
    care_action = "view"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_active and "pk" in kwargs:
            access.patient_for(request.user, kwargs["pk"], self.care_action)
        return super().dispatch(request, *args, **kwargs)

    def patient(self, request, pk):
        return access.patient_for(request.user, pk, self.care_action)[0]

    def page(self, request, template, **context):
        return render(
            request,
            f"pages/CuidadosApp/{template}.html",
            {
                "capacity": capacity_state(request.user),
                "server_now": timezone.now(),
                **context,
            },
        )

    def form_page(
        self,
        request,
        title,
        form,
        patient=None,
        help_text="",
        button="Guardar",
        **context,
    ):
        return self.page(
            request,
            "form",
            title=title,
            form=form,
            patient=patient,
            help_text=help_text,
            button=button,
            **context,
        )


class PanelView(CareView):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        patients = list(
            Patient.objects.filter(
                pk__in=access.active_ids_for(request.user)
            ).select_related("timer__last_event")
        )
        chosen = request.GET.get("patient")
        selected = (
            next((p for p in patients if str(p.pk) == chosen), None)
            if chosen
            else next(iter(patients), None)
        )
        if chosen and selected is None:
            raise Http404
        guide = None
        if selected:
            timer = getattr(selected, "timer", None)
            code = (
                timer.last_event.snapshot.get("guide")
                if timer and timer.last_event
                else "supina"
            )
            guide = CareGuide.objects.filter(code=code, active=True).first()
        return self.page(
            request,
            "panel",
            patients=patients,
            selected=selected,
            guide=guide,
            agenda=agenda(
                request.user, patient_id=selected.pk if chosen and selected else None
            ),
            events=CareEvent.objects.filter(
                patient_id__in=access.active_ids_for(
                    request.user, roles=access.ACTIONS["history"]
                )
            ).select_related("patient")[:5],
        )


class PatientListView(CareView):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        active = set(access.active_ids_for(request.user))
        roles = access.roles_for(request.user)
        patients = list(
            access.accessible_patients(request.user).select_related(
                "timer__last_event"
            )
        )
        for patient in patients:
            patient.eligible = patient.pk in active
            patient.role = roles[patient.pk]
        return self.page(request, "patients", patients=patients)


class PatientFormView(CareView):
    care_action = "edit_patient"

    def get(self, request, pk=None):
        patient = self.patient(request, pk) if pk else None
        form = (forms.PatientForm if pk else forms.NewPatientForm)(
            instance=patient, initial={"version": patient.version if patient else 0}
        )
        return self.form_page(
            request,
            "Editar ficha" if pk else "Registrar paciente",
            form,
            patient,
            "Esta demo utiliza datos ficticios. El paciente quedará asociado a tu cuenta.",
        )

    def post(self, request, pk=None):
        patient = self.patient(request, pk) if pk else None
        form = (forms.PatientForm if pk else forms.NewPatientForm)(
            request.POST, instance=patient
        )
        if form.is_valid():
            try:
                patient = services.save_patient(
                    request.user,
                    form.cleaned_data,
                    pk,
                    form.cleaned_data.get("version"),
                )
            except (ValidationError, DatabaseError) as error:
                form_error(form, error)
            else:
                messages.success(request, "Ficha guardada.")
                return redirect("CuidadosApp:patient", pk=patient.pk)
        return self.form_page(
            request, "Editar ficha" if pk else "Registrar paciente", form, patient
        )


class PatientDetailView(CareView):
    http_method_names = ["get", "head", "options"]

    def get(self, request, pk):
        patient, role = access.patient_for(request.user, pk, "view")
        can = {action: True for action in access.allowed_actions(role)}
        timer = (
            PostureTimer.objects.filter(patient=patient)
            .select_related("last_event")
            .first()
        )
        kind = "archive" if patient.active else "reactivate"
        return self.page(
            request,
            "patient",
            patient=patient,
            role=role,
            can=can,
            timer=timer,
            eligible=pk in access.active_ids_for(request.user),
            archive_token=services.action_token(
                request.user, patient, kind, version=patient.version
            )
            if "archive" in can
            else "",
            medications=patient.medications.prefetch_related("times").all(),
            tasks=patient.tasks.all(),
            # D-062: a caregiver sees today's agenda and the last posture only.
            events=patient.events.all()[:8] if "history" in can else [],
            accesses=patient.accesses.filter(revoked_at__isnull=True).select_related(
                "user"
            )
            if "manage_access" in can
            else [],
            invitations=invitations.pending(patient) if "manage_access" in can else [],
            **privacy_context(patient, can),
        )


class ArchiveView(CareView):
    http_method_names = ["post", "options"]
    care_action = "archive"
    activate = False

    def post(self, request, pk):
        try:
            services.set_patient_active(
                request.user, pk, request.POST.get("token", ""), self.activate
            )
        except (ValidationError, DatabaseError) as error:
            messages.error(
                request,
                error.messages[0]
                if isinstance(error, ValidationError)
                else "No se pudo cambiar el estado.",
            )
        else:
            messages.success(
                request,
                "Paciente reactivado. Inicia sus recordatorios cuando corresponda."
                if self.activate
                else "Paciente archivado. Ficha e historial conservados; recordatorios pausados.",
            )
        return redirect("CuidadosApp:patient", pk=pk)


class ReactivateView(ArchiveView):
    activate = True


class DailyFormView(CareView):
    care_action = "configure"
    task = False

    def form_context(self, request, pk, object_pk, data=None):
        patient = self.patient(request, pk)
        obj = (
            get_object_or_404(
                CareTask if self.task else Medication, pk=object_pk, patient=patient
            )
            if object_pk
            else None
        )
        form = (forms.TaskForm if self.task else forms.MedicationForm)(
            data, instance=obj, initial={"version": obj.version if obj else 0}
        )
        return patient, obj, form

    def show(self, request, patient, form):
        return self.form_page(
            request,
            "Cuidado diario" if self.task else "Medicamento y horarios",
            form,
            patient,
            "Define el horario diario en Santiago. Editar afecta próximos horarios y conserva lo ya registrado."
            if self.task
            else "Escribe la dosis indicada en el plan del paciente. La plataforma no prescribe ni calcula dosis. Editar conserva los registros anteriores.",
        )

    def get(self, request, pk, object_pk=None):
        patient, _, form = self.form_context(request, pk, object_pk)
        return self.show(request, patient, form)

    def post(self, request, pk, object_pk=None):
        patient, _, form = self.form_context(request, pk, object_pk, request.POST)
        if form.is_valid():
            try:
                services.save_daily(request.user, pk, form, object_pk, self.task)
            except (ValidationError, DatabaseError) as error:
                form_error(form, error)
            else:
                messages.success(
                    request,
                    "Cuidado guardado."
                    if self.task
                    else "Medicamento y horarios guardados.",
                )
                return redirect("CuidadosApp:patient", pk=pk)
        return self.show(request, patient, form)


class TaskFormView(DailyFormView):
    task = True


class PostureView(CareView):
    care_action = "record"

    def get(self, request, pk):
        patient = self.patient(request, pk)
        timer = PostureTimer.objects.filter(patient=patient).first()
        form = forms.PostureForm(
            initial={
                "token": services.action_token(
                    request.user,
                    patient,
                    "posture",
                    version=timer.generation if timer else 0,
                ),
                "interval": timer.interval if timer else 120,
            }
        )
        return self.form_page(
            request,
            "Registrar cambio de postura",
            form,
            patient,
            "Confirma únicamente una postura que ya realizaste. El próximo cambio se calcula desde esta confirmación. Usa el intervalo acordado en el plan individual.",
            "Registrar postura",
        )

    def post(self, request, pk):
        patient = self.patient(request, pk)
        form = forms.PostureForm(request.POST)
        if form.is_valid():
            try:
                services.record_posture(request.user, pk, **form.cleaned_data)
            except (ValidationError, DatabaseError) as error:
                form_error(form, error)
            else:
                messages.success(
                    request, "Postura registrada y próximo cambio programado."
                )
                return redirect("CuidadosApp:patient", pk=pk)
        return self.form_page(
            request,
            "Registrar cambio de postura",
            form,
            patient,
            button="Registrar postura",
        )


class TimerView(CareView):
    care_action = "record"

    def get(self, request, pk):
        patient = self.patient(request, pk)
        timer = PostureTimer.objects.filter(patient=patient).first()
        form = forms.TimerForm(
            initial={
                "token": services.action_token(
                    request.user, patient, "timer", version=timer.generation if timer else 0
                ),
                "interval": timer.interval if timer else 120,
                "action": "interval" if timer else "start",
            },
            timer=timer,
        )
        return self.form_page(
            request,
            "Configurar recordatorios de postura",
            form,
            patient,
            "Crear recordatorio inicia un reloj sin registrar un cuidado. Cambiar intervalo cuenta desde la última postura o el inicio del reloj y puede dejar un cambio pendiente. Pausar detiene avisos; reanudar inicia un intervalo desde ahora y no registra una postura.",
            "Confirmar configuración",
        )

    def post(self, request, pk):
        patient = self.patient(request, pk)
        form = forms.TimerForm(
            request.POST, timer=PostureTimer.objects.filter(patient=patient).first()
        )
        if form.is_valid():
            try:
                services.configure_timer(request.user, pk, **form.cleaned_data)
            except (ValidationError, DatabaseError) as error:
                form_error(form, error)
            else:
                messages.success(
                    request,
                    "Recordatorios actualizados; no se registró una postura nueva.",
                )
                return redirect("CuidadosApp:patient", pk=pk)
        return self.form_page(
            request, "Configurar recordatorios de postura", form, patient
        )


class AgendaView(CareView):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        pk = request.GET.get("patient")
        patient = access.patient_for(request.user, pk, "view")[0] if pk else None
        return self.page(
            request,
            "agenda",
            agenda=agenda(request.user, patient_id=patient.pk if patient else None),
            patient=patient,
            patients=Patient.objects.filter(pk__in=access.active_ids_for(request.user)),
        )


class DailyEventView(CareView):
    care_action = "record"

    def show(self, request, pk, form):
        patient = self.patient(request, pk)
        data = services.read_action(request.user, form["token"].value() or "", patient)
        if data["kind"] not in ("care", "medication"):
            raise ValidationError("Esta actividad no corresponde a la agenda.")
        obj = get_object_or_404(
            CareTask if data["kind"] == "care" else Medication,
            pk=data["subject"],
            patient=patient,
        )
        return self.form_page(
            request,
            f"Registrar: {obj.name}",
            form,
            patient,
            "Confirma lo que realizaste u omitiste. Leer un recordatorio no registra esta actividad.",
            "Confirmar registro",
        )

    def get(self, request, pk):
        form = forms.EventForm(initial={"token": request.GET.get("token", "")})
        try:
            return self.show(request, pk, form)
        except ValidationError as error:
            messages.error(request, error.messages[0])
            return redirect("CuidadosApp:agenda")

    def post(self, request, pk):
        patient = self.patient(request, pk)
        form = forms.EventForm(request.POST)
        if form.is_valid():
            try:
                services.record_daily(request.user, pk, **form.cleaned_data)
            except (ValidationError, DatabaseError) as error:
                form_error(form, error)
            else:
                messages.success(request, "Actividad registrada.")
                return redirect("CuidadosApp:agenda")
        try:
            return self.show(request, pk, form)
        except ValidationError:
            return self.form_page(request, "Revisar actividad", form, patient)


class HistoryView(CareView):
    http_method_names = ["get", "head", "options"]
    care_action = "history"

    def get(self, request, pk):
        from django.core.paginator import Paginator

        patient = self.patient(request, pk)
        events = patient.events.select_related("corrected_event", "author").all()
        return self.page(
            request,
            "history",
            patient=patient,
            events=Paginator(events, 20).get_page(request.GET.get("page")),
        )


class CorrectionView(CareView):
    care_action = "correct"

    def event(self, request, pk, event_pk):
        patient, role = access.patient_for(request.user, pk, self.care_action)
        event = get_object_or_404(CareEvent, pk=event_pk, patient=patient)
        if role == access.CUIDADOR and event.author_id != request.user.pk:
            raise PermissionDenied
        return patient, event

    def get(self, request, pk, event_pk):
        patient, event = self.event(request, pk, event_pk)
        form = forms.CorrectionForm(
            initial={
                "token": services.action_token(
                    request.user, patient, "correction", subject=event.pk
                )
            }
        )
        return self.form_page(
            request,
            "Añadir corrección",
            form,
            patient,
            "La nota se vincula al registro original; no modifica la alarma ni borra lo registrado.",
            "Guardar corrección",
        )

    def post(self, request, pk, event_pk):
        patient, _ = self.event(request, pk, event_pk)
        form = forms.CorrectionForm(request.POST)
        if form.is_valid():
            try:
                services.correct_event(request.user, pk, event_pk, **form.cleaned_data)
            except (ValidationError, DatabaseError) as error:
                form_error(form, error)
            else:
                messages.success(
                    request, "Corrección vinculada; registro original conservado."
                )
                return redirect("CuidadosApp:history", pk=pk)
        return self.form_page(request, "Añadir corrección", form, patient)


class GuidesView(CareView):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        return self.page(
            request, "guides", guides=CareGuide.objects.filter(active=True)
        )


class SelectionView(CareView):
    def future(self, request):
        sub = Subscription.objects.filter(user=request.user).first()
        return bool(
            sub and sub.cancel_at_period_end and sub.end and sub.end > timezone.now()
        )

    def get(self, request):
        sub = Subscription.objects.filter(user=request.user).first()
        state = capacity_state(request.user)
        future = self.future(request)
        if not state["pending"] and not future:
            return redirect("CuidadosApp:panel")
        token = services.action_token(
            request.user,
            None,
            "selection",
            version=sub.version if sub else 0,
            offered=[list(row) for row in fingerprint(request.user)],
            future=future,
        )
        form = forms.SelectionForm(
            user=request.user,
            initial={
                "token": token,
                "patients": state["selection"].patients if state["selection"] else [],
            },
        )
        return self.show(request, form, future)

    def show(self, request, form, future):
        state = capacity_state(request.user)
        return self.form_page(
            request,
            "Elige tus pacientes activos",
            form,
            help_text=f"Elige hasta {1 if future else state['limit']} paciente(s). Los demás quedarán archivados con su ficha e historial. "
            + (
                "La selección se aplicará al terminar el período; hasta entonces conservarás todos tus cuidados."
                if future
                else "La selección se aplicará al confirmar."
            ),
            button="Confirmar pacientes activos",
        )

    def post(self, request):
        form = forms.SelectionForm(request.POST, user=request.user)
        future = self.future(request)
        if form.is_valid():
            try:
                data = services.read_action(
                    request.user, form.cleaned_data["token"], kind="selection"
                )
                if data["future"] != future:
                    raise ValidationError(
                        "El período cambió; recarga y revisa la selección."
                    )
                choose_capacity(
                    request.user,
                    list(form.cleaned_data["patients"].values_list("pk", flat=True)),
                    data["offered"],
                    data["version"],
                    future,
                )
            except (ValidationError, DatabaseError) as error:
                form_error(form, error)
            else:
                messages.success(
                    request,
                    "Selección guardada para el final del período."
                    if future
                    else "Pacientes activos seleccionados; historial conservado.",
                )
                return redirect("CuidadosApp:panel")
        return self.show(request, form, future)


class RemindersView(CareView):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        state = capacity_state(request.user)
        ids = access.active_ids_for(request.user, roles=access.RECIPIENTS["care"])
        return JsonResponse(
            {
                "now": timezone.now().isoformat(),
                "pending_selection": state["pending"],
                "reminders": reminders(request.user),
                "timers": [
                    {
                        "patient": t.patient_id,
                        "due": t.next_due_at.isoformat()
                        if t.next_due_at and not t.paused
                        else None,
                        "generation": t.generation,
                        "paused": t.paused,
                    }
                    for t in PostureTimer.objects.filter(patient_id__in=ids)
                ],
            }
        )


class ClaimView(CareView):
    http_method_names = ["post", "options"]

    def post(self, request):
        try:
            created = claim_reminder(request.user, request.POST.get("token", ""))
        except ValidationError as error:
            return JsonResponse({"error": error.messages[0]}, status=409)
        except DatabaseError:
            return JsonResponse({"error": "No se pudo confirmar el aviso."}, status=503)
        return JsonResponse({"claimed": created})


class AccessView(CareView):
    """Titular creates a code; it is shown once and never stored in clear."""

    http_method_names = ["post", "options"]
    care_action = "manage_access"

    def post(self, request, pk):
        patient = self.patient(request, pk)
        form = forms.InviteForm(request.POST)
        try:
            if not form.is_valid():
                raise ValidationError("Elige el rol de la persona invitada.")
            invitation, code = invitations.create_invitation(
                request.user, pk, form.cleaned_data["role"]
            )
        except (ValidationError, DatabaseError) as error:
            messages.error(
                request,
                error.messages[0]
                if isinstance(error, ValidationError)
                else "No se pudo crear el código.",
            )
            return redirect("CuidadosApp:patient", pk=pk)
        return self.page(
            request,
            "access_code",
            patient=patient,
            invitation=invitation,
            code=code,
        )


class RevokeAccessView(CareView):
    http_method_names = ["post", "options"]
    invitation = False

    def post(self, request, object_pk):
        model = PatientInvitation if self.invitation else PatientAccess
        pk = get_object_or_404(model, pk=object_pk).patient_id
        try:
            (
                invitations.revoke_invitation
                if self.invitation
                else invitations.revoke_access
            )(
                request.user, object_pk
            )
        except DatabaseError:
            messages.error(request, "No se pudo revocar. Inténtalo nuevamente.")
        else:
            messages.success(
                request,
                "Código anulado."
                if self.invitation
                else "Acceso revocado. Sus registros anteriores se conservan.",
            )
        return redirect("CuidadosApp:patient", pk=pk)


class RevokeInvitationView(RevokeAccessView):
    invitation = True


class JoinView(CareView):
    def show(self, request, form, preview=None):
        return self.form_page(
            request,
            "Unirme con un código",
            form,
            help_text=(
                f"Te unirás a {preview['patient_name']} como "
                f"{preview['role']}. Confirma para continuar."
                if preview
                else "Ingresa el código que te entregó la persona responsable del paciente."
            ),
            button="Confirmar y unirme" if preview else "Revisar código",
        )

    def get(self, request):
        return self.show(request, forms.JoinForm())

    def post(self, request):
        form = forms.JoinForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            try:
                if form.cleaned_data["confirm"] == "1":
                    link = invitations.accept(request.user, code)
                    messages.success(
                        request, "Listo. Ya puedes acompañar a este paciente."
                    )
                    return redirect("CuidadosApp:patient", pk=link.patient_id)
                found = invitations.preview(request.user, code)
            except (ValidationError, DatabaseError) as error:
                form_error(form, error)
                form.data = form.data.copy()
                form.data["confirm"] = ""
            else:
                confirmation = forms.JoinForm(
                    initial={"code": code, "confirm": "1"}, confirming=True
                )
                return self.show(request, confirmation, found)
        return self.show(request, form)


class LeaveView(CareView):
    http_method_names = ["post", "options"]
    care_action = "leave"

    def post(self, request, pk):
        try:
            invitations.leave(request.user, pk)
        except DatabaseError:
            messages.error(request, "No se pudo completar. Inténtalo nuevamente.")
            return redirect("CuidadosApp:patient", pk=pk)
        messages.success(request, "Dejaste de acompañar a este paciente.")
        return redirect("CuidadosApp:patients")
