from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.utils import timezone

from CuidadosApp import access, capacity, forms, scheduling, services
from CuidadosApp.models import (
    CareEvent,
    CareGuide,
    CareTask,
    Medication,
    Patient,
    PostureTimer,
)
from PlanesApp.entitlements import capabilities, mobile_capabilities
from PrivacidadApp.names import author_name

from .base import MobileView
from .detection import camera_state


def patient_data(p):
    return {
        key: getattr(p, key)
        for key in (
            "id",
            "name",
            "birth_date",
            "notes",
            "contact_name",
            "contact_phone",
            "contact_relation",
            "active",
            "version",
        )
    }


def patient_payload(p, role, active_ids):
    """Patient fields plus the caller's role; the server still enforces each action."""
    return {
        **patient_data(p),
        "role": role,
        "allowed_actions": access.allowed_actions(role),
        "eligible": p.pk in active_ids,
    }


def event_data(e, user):
    return {
        "id": e.pk,
        "kind": e.kind,
        "status": e.status,
        "occurred_at": e.occurred_at,
        "author": author_name(e.author),
        "note": e.note,
        "label": e.snapshot.get("label", ""),
        "dose": e.snapshot.get("dose", ""),
        "corrected_event_id": e.corrected_event_id,
        "token": services.action_token(user, e.patient, "correction", e.pk),
    }


def daily_data(obj):
    data = {
        key: getattr(obj, key)
        for key in (
            "id",
            "name",
            "notes",
            "start_date",
            "end_date",
            "active",
            "version",
        )
    }
    if isinstance(obj, Medication):
        data.update(
            dose=obj.dose,
            hours=", ".join(t.time.strftime("%H:%M") for t in obj.times.all()),
        )
    else:
        data["time"] = obj.time.strftime("%H:%M") if obj.time else ""
    return data


class MeView(MobileView):
    def get(self, request):
        return JsonResponse(
            {
                "username": request.user.username,
                "name": request.user.get_full_name() or request.user.username,
                "capabilities": mobile_capabilities(request.user),
                "server_time": timezone.now(),
                "timezone": "America/Santiago",
            }
        )


class CapabilitiesView(MobileView):
    def get(self, request):
        return JsonResponse(mobile_capabilities(request.user))


class PatientsView(MobileView):
    def get(self, request):
        state = capacity.capacity_state(request.user)
        roles = access.roles_for(request.user)
        active = set(access.active_ids_for(request.user))
        return JsonResponse(
            {
                "patients": [
                    patient_payload(p, roles[p.pk], active)
                    for p in access.accessible_patients(request.user)
                ],
                "capacity": {
                    k: state[k] for k in ("limit", "active_ids", "pending", "count")
                },
                "fingerprint": capacity.fingerprint(request.user),
                "subscription_version": capabilities(request.user)["version"],
            }
        )

    def post(self, request):
        form = self.validated(forms.NewPatientForm(self.data))
        return JsonResponse(
            patient_data(services.save_patient(request.user, form.cleaned_data)),
            status=201,
        )


class PatientView(MobileView):
    def get(self, request, pk):
        p, role = access.patient_for(request.user, pk, "view")
        timer = PostureTimer.objects.filter(patient=p).first()
        generation = timer.generation if timer else 0
        data = patient_payload(p, role, access.active_ids_for(request.user))
        kinds = ["posture", "timer"]
        if role in access.ACTIONS["archive"]:
            kinds += ["archive", "reactivate"]
        data["tokens"] = {
            kind: services.action_token(
                request.user,
                p,
                kind,
                version=generation if kind in ("posture", "timer") else p.version,
            )
            for kind in kinds
        }
        data["timer"] = (
            {
                "interval": timer.interval,
                "paused": timer.paused,
                "next_due_at": timer.next_due_at,
                "generation": timer.generation,
            }
            if timer
            else None
        )
        data["server_time"] = timezone.now()
        data["camera_state"] = camera_state(p)
        return JsonResponse(data)

    def post(self, request, pk):
        p, _ = access.patient_for(request.user, pk, "edit_patient")
        form = self.validated(forms.PatientForm(self.data, instance=p))
        return JsonResponse(
            patient_data(
                services.save_patient(
                    request.user, form.cleaned_data, pk, form.cleaned_data["version"]
                )
            )
        )


class ActiveView(MobileView):
    def post(self, request, pk, action):
        if action not in ("archive", "reactivate"):
            raise Http404
        p = services.set_patient_active(
            request.user, pk, self.data["token"], action == "reactivate"
        )
        p.refresh_from_db()
        return JsonResponse(patient_data(p))


class DailyView(MobileView):
    def get(self, request, pk, kind):
        if kind not in ("tasks", "medications"):
            raise Http404
        p, _ = access.patient_for(request.user, pk, "view")
        model = CareTask if kind == "tasks" else Medication
        return JsonResponse(
            {"items": [daily_data(obj) for obj in model.objects.filter(patient=p)]}
        )

    def post(self, request, pk, kind, object_pk=None):
        if kind not in ("tasks", "medications"):
            raise Http404
        p, _ = access.patient_for(request.user, pk, "configure")
        task = kind == "tasks"
        model = CareTask if task else Medication
        obj = get_object_or_404(model, pk=object_pk, patient=p) if object_pk else None
        form = self.validated(
            (forms.TaskForm if task else forms.MedicationForm)(self.data, instance=obj)
        )
        return JsonResponse(
            daily_data(services.save_daily(request.user, pk, form, object_pk, task)),
            status=200 if obj else 201,
        )


class AgendaView(MobileView):
    def get(self, request):
        pid = request.GET.get("patient")
        if pid:
            pid = access.patient_for(request.user, pid, "view")[0].pk
        items = []
        for i in scheduling.agenda(request.user, patient_id=pid):
            items.append(
                {
                    "key": i["key"],
                    "kind": i["kind"],
                    "patient_id": i["patient"].pk,
                    "patient": i["patient"].name,
                    "label": i["label"],
                    "dose": i["dose"],
                    "due": i["due"],
                    "token": i["token"],
                    "overdue": i["overdue"],
                    "status": i["event"].status if i["event"] else "pending",
                }
            )
        return JsonResponse({"items": items, "server_time": timezone.now()})


class EventView(MobileView):
    def post(self, request, pk):
        data = self.validated(forms.EventForm(self.data)).cleaned_data
        event = services.record_daily(
            request.user, pk, data["token"], data["status"], data["note"]
        )
        return JsonResponse(event_data(event, request.user))


class PostureView(MobileView):
    def post(self, request, pk):
        d = self.validated(forms.PostureForm(self.data)).cleaned_data
        e = services.record_posture(
            request.user, pk, d["token"], d["guide"], d["interval"], d["note"]
        )
        return JsonResponse(event_data(e, request.user))


class TimerView(MobileView):
    def post(self, request, pk):
        d = self.validated(forms.TimerForm(self.data)).cleaned_data
        services.configure_timer(
            request.user, pk, d["token"], d["action"], d["interval"]
        )
        return JsonResponse({"saved": True})


class HistoryView(MobileView):
    def get(self, request, pk):
        p, _ = access.patient_for(request.user, pk, "history")
        page = max(1, int(request.GET.get("page", 1)))
        rows = list(
            CareEvent.objects.filter(patient=p).select_related("author")[
                (page - 1) * 30 : page * 30 + 1
            ]
        )
        return JsonResponse(
            {
                "items": [event_data(e, request.user) for e in rows[:30]],
                "next_page": page + 1 if len(rows) > 30 else None,
            }
        )


class CorrectionView(MobileView):
    def post(self, request, pk, event_pk):
        d = self.validated(forms.CorrectionForm(self.data)).cleaned_data
        e = services.correct_event(request.user, pk, event_pk, d["token"], d["note"])
        return JsonResponse(event_data(e, request.user))


class GuidesView(MobileView):
    def get(self, request):
        return JsonResponse(
            {
                "items": [
                    {
                        "id": g.pk,
                        "code": g.code,
                        "title": g.title,
                        "category": g.category,
                        "instructions": g.instructions,
                        "precautions": g.precautions,
                        "image": static(g.illustration["image"]),
                        "image_alt": g.illustration["alt"],
                        "source_title": g.source_title,
                        "source_url": g.source_url,
                    }
                    for g in CareGuide.objects.filter(active=True)
                ]
            }
        )


class RemindersView(MobileView):
    def get(self, request):
        return JsonResponse({"items": scheduling.reminders(request.user)})

    def post(self, request):
        return JsonResponse(
            {"claimed": scheduling.claim_reminder(request.user, self.data["token"])}
        )


class CapacityView(MobileView):
    def post(self, request):
        capacity.choose_capacity(
            request.user,
            self.data["patients"],
            self.data["fingerprint"],
            self.data["version"],
        )
        return JsonResponse({"saved": True})


class TimerScheduleView(MobileView):
    """Only eligible owned timers; no names/clinical data in local notifications."""
    def get(self, request):
        ids = access.active_ids_for(request.user, roles=access.RECIPIENTS["care"])
        rows = PostureTimer.objects.filter(patient_id__in=ids, paused=False, next_due_at__isnull=False)
        return JsonResponse({"items": [{"id": t.patient_id, "generation": t.generation,
            "due": t.next_due_at} for t in rows], "server_time": timezone.now()})
