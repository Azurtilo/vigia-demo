from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from PlanesApp.models import Subscription

from . import forms, services
from .capacity import capacity_state, choose_capacity, fingerprint
from .models import CareEvent, CareGuide, CareTask, Medication, Patient, PostureTimer
from .permissions import CareOwnerMixin
from .scheduling import agenda, claim_reminder, reminders


def form_error(form, error):
    form.add_error(
        None,
        error
        if isinstance(error, ValidationError)
        else "No se pudo guardar. Ningún cambio se confirmó; inténtalo nuevamente.",
    )


@method_decorator(never_cache, name="dispatch")
class CareView(CareOwnerMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_active and "pk" in kwargs:
            services.own_patient(request.user, kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

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
        state = capacity_state(request.user)
        patients = list(
            Patient.objects.filter(
                owner=request.user, pk__in=state["active_ids"]
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
            events=CareEvent.objects.filter(patient__owner=request.user).select_related(
                "patient"
            )[:5],
        )


class PatientListView(CareView):
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        state = capacity_state(request.user)
        patients = list(
            Patient.objects.filter(owner=request.user).select_related(
                "timer__last_event"
            )
        )
        for patient in patients:
            patient.eligible = patient.pk in state["active_ids"]
        return self.page(request, "patients", patients=patients)


class PatientFormView(CareView):
    def get(self, request, pk=None):
        patient = services.own_patient(request.user, pk) if pk else None
        form = forms.PatientForm(
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
        patient = services.own_patient(request.user, pk) if pk else None
        form = forms.PatientForm(request.POST, instance=patient)
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
        patient = services.own_patient(request.user, pk)
        timer = (
            PostureTimer.objects.filter(patient=patient)
            .select_related("last_event")
            .first()
        )
        state = capacity_state(request.user)
        kind = "archive" if patient.active else "reactivate"
        return self.page(
            request,
            "patient",
            patient=patient,
            timer=timer,
            eligible=pk in state["active_ids"],
            archive_token=services.action_token(
                request.user, patient, kind, version=patient.version
            ),
            medications=patient.medications.prefetch_related("times").all(),
            tasks=patient.tasks.all(),
            events=patient.events.all()[:8],
        )


class ArchiveView(CareView):
    http_method_names = ["post", "options"]
    activate = False

    def post(self, request, pk):
        services.own_patient(request.user, pk)
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
    task = False

    def form_context(self, request, pk, object_pk, data=None):
        patient = services.own_patient(request.user, pk)
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
    def get(self, request, pk):
        patient = services.own_patient(request.user, pk)
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
        patient = services.own_patient(request.user, pk)
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
    def get(self, request, pk):
        patient = services.own_patient(request.user, pk)
        timer = PostureTimer.objects.filter(patient=patient).first()
        form = forms.TimerForm(
            initial={
                "token": services.action_token(
                    request.user, patient, "timer", version=timer.generation if timer else 0
                ),
                "interval": timer.interval if timer else 120,
                "action": "interval" if timer else "start",
            }
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
        patient = services.own_patient(request.user, pk)
        form = forms.TimerForm(request.POST)
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
        patient = services.own_patient(request.user, pk) if pk else None
        return self.page(
            request,
            "agenda",
            agenda=agenda(request.user, patient_id=patient.pk if patient else None),
            patient=patient,
            patients=Patient.objects.filter(
                owner=request.user, pk__in=capacity_state(request.user)["active_ids"]
            ),
        )


class DailyEventView(CareView):
    def show(self, request, pk, form):
        patient = services.own_patient(request.user, pk)
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
        services.own_patient(request.user, pk)
        form = forms.EventForm(initial={"token": request.GET.get("token", "")})
        try:
            return self.show(request, pk, form)
        except ValidationError as error:
            messages.error(request, error.messages[0])
            return redirect("CuidadosApp:agenda")

    def post(self, request, pk):
        patient = services.own_patient(request.user, pk)
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

    def get(self, request, pk):
        from django.core.paginator import Paginator

        patient = services.own_patient(request.user, pk)
        events = patient.events.select_related("corrected_event", "author").all()
        return self.page(
            request,
            "history",
            patient=patient,
            events=Paginator(events, 20).get_page(request.GET.get("page")),
        )


class CorrectionView(CareView):
    def get(self, request, pk, event_pk):
        patient = services.own_patient(request.user, pk)
        event = get_object_or_404(CareEvent, pk=event_pk, patient=patient)
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
        patient = services.own_patient(request.user, pk)
        get_object_or_404(CareEvent, pk=event_pk, patient=patient)
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
                    for t in PostureTimer.objects.filter(
                        patient__owner=request.user, patient_id__in=state["active_ids"]
                    )
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
