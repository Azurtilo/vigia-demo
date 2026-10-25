"""Delegated-care endpoints (spec 013): codes, links and the caregiver summary."""

from django.http import JsonResponse

from CuidadosApp import access, invitations, scheduling
from CuidadosApp.models import PostureTimer

from PrivacidadApp.names import author_name

from .base import MobileView


def link_data(link):
    return {
        "id": link.pk,
        "name": author_name(link.user),
        "role": link.role,
        "accepted_at": link.accepted_at,
    }


class AccessListView(MobileView):
    def get(self, request, pk):
        patient, _ = access.patient_for(request.user, pk, "manage_access")
        return JsonResponse(
            {
                "accesses": [
                    link_data(link)
                    for link in patient.accesses.filter(
                        revoked_at__isnull=True
                    ).select_related("user")
                ],
                "invitations": [
                    {"id": i.pk, "role": i.role, "expires_at": i.expires_at}
                    for i in invitations.pending(patient)
                ],
            }
        )

    def post(self, request, pk):
        invitation, code = invitations.create_invitation(
            request.user, pk, self.data.get("role")
        )
        return JsonResponse(
            {
                "id": invitation.pk,
                "role": invitation.role,
                "code": code,
                "expires_at": invitation.expires_at,
            },
            status=201,
        )


class RevokeAccessView(MobileView):
    def post(self, request, object_pk):
        invitations.revoke_access(request.user, object_pk)
        return JsonResponse({"revoked": True})


class RevokeInvitationView(MobileView):
    def post(self, request, object_pk):
        invitations.revoke_invitation(request.user, object_pk)
        return JsonResponse({"revoked": True})


class PreviewView(MobileView):
    def post(self, request):
        return JsonResponse(invitations.preview(request.user, self.data.get("code")))


class AcceptView(MobileView):
    def post(self, request):
        link = invitations.accept(request.user, self.data.get("code"))
        return JsonResponse(
            {"patient_id": link.patient_id, "role": link.role}, status=201
        )


class LeaveView(MobileView):
    def post(self, request, pk):
        invitations.leave(request.user, pk)
        return JsonResponse({"left": True})


class SummaryView(MobileView):
    """D-062: today's agenda and the last posture, without the full history."""

    def get(self, request, pk):
        patient, role = access.patient_for(request.user, pk, "view")
        timer = (
            PostureTimer.objects.filter(patient=patient)
            .select_related("last_event")
            .first()
        )
        last = timer.last_event if timer else None
        return JsonResponse(
            {
                "role": role,
                "last_posture": {
                    "label": last.snapshot.get("label", ""),
                    "occurred_at": last.occurred_at,
                }
                if last
                else None,
                "agenda": [
                    {
                        "key": i["key"],
                        "kind": i["kind"],
                        "label": i["label"],
                        "dose": i["dose"],
                        "due": i["due"],
                        "token": i["token"],
                        "overdue": i["overdue"],
                        "status": i["event"].status if i["event"] else "pending",
                    }
                    for i in scheduling.agenda(request.user, patient_id=patient.pk)
                ],
            }
        )

