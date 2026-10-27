import hashlib
import json
import logging
import math
import secrets
import uuid
from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from CuidadosApp.capacity import capacity_state
from CuidadosApp.mobile_models import MONITOR_STATES
from CuidadosApp.models import DetectionNode, PostureObservation
from CuidadosApp import push
from CuidadosApp.access import patient_for
from PrivacidadApp import consent
from CuidadosApp.services import acting, digest
from PlanesApp.entitlements import capabilities
from PlanesApp.services import locked_user

from .base import MobileView, error

log = logging.getLogger("vigia.edge")
# Risk events keep their original time when delivered late; the node stops at 55 min.
RISK_MAX_AGE = timedelta(hours=1)
CONNECTED_FOR = timedelta(seconds=90)
MONITOR_VALUES = {value for value, _ in MONITOR_STATES}


def monitor_state_param(request):
    """Spec 017 (D-073): optional ?monitor_state= on the renewal; None if absent."""
    if set(request.GET) - {"monitor_state"}:
        raise ValidationError("Parámetro no admitido en la renovación del nodo.")
    values = request.GET.getlist("monitor_state")
    if not values:
        return None
    if len(values) > 1 or values[0] not in MONITOR_VALUES:
        raise ValidationError("Estado de monitoreo inválido.")
    return values[0]


def allowed(user, patient):
    """Detection follows the titular's plan and capacity (spec 013)."""
    titular = patient.owner
    if not user.is_active or not capabilities(titular)["features"]["posture_detection"]:
        raise PermissionDenied
    if patient.pk not in capacity_state(titular)["active_ids"]:
        raise PermissionDenied
    if consent.enforced() and not consent.active(patient, "deteccion"):
        raise PermissionDenied  # spec 014: the node stops (fail-closed)


def node_data(node):
    return {
        "id": str(node.pk),
        "name": node.name,
        "active": node.active,
        "last_seen_at": node.last_seen_at,
        "connected": bool(
            node.active
            and node.last_seen_at
            and node.last_seen_at > timezone.now() - CONNECTED_FOR
        ),
        "monitor_state": node.monitor_state or "desconocido",
        "monitor_since": node.monitor_since,
    }


# Spec 017 (D-077): worst state first when a patient has several nodes.
CAMERA_PRIORITY = ["sin_senal", "sin_imagen", "poca_luz", "persona_no_visible", "normal"]


def camera_state(patient):
    """Aggregated, read-only state for every role with `view`; no node details.

    None without active nodes, without detection in the titular's plan, or when
    no node ever reported a state (versions before spec 017).
    """
    if not capabilities(patient.owner)["features"]["posture_detection"]:
        return None
    states = set()
    for node in patient.detection_nodes.filter(active=True):
        data = node_data(node)
        states.add(data["monitor_state"] if data["connected"] else "sin_senal")
    return next((s for s in CAMERA_PRIORITY if s in states), None)


class NodesView(MobileView):
    def get(self, request, pk):
        p, _ = patient_for(request.user, pk, "manage_nodes")
        return JsonResponse({"items": [node_data(n) for n in p.detection_nodes.all()]})

    @transaction.atomic
    def post(self, request, pk):
        user, _, p, _ = acting(request.user, pk, "manage_nodes")
        consent.require(p, "deteccion")
        allowed(user, p)
        name = self.data.get("name", "")
        if not isinstance(name, str):
            raise ValidationError("El nombre debe ser texto.")
        name = name.strip()
        if not 1 <= len(name) <= 80:
            raise ValidationError("Escribe un nombre de hasta 80 caracteres.")
        # One active camera per patient is the pilot's explicit technical limit.
        if p.detection_nodes.filter(active=True).exists():
            raise ValidationError("Revoca el nodo anterior antes de vincular otro.")
        token = secrets.token_urlsafe(32)
        node = DetectionNode.objects.create(
            patient=p,
            name=name,
            credential_hash=hashlib.sha256(token.encode()).hexdigest(),
        )
        return JsonResponse({**node_data(node), "credential": token}, status=201)


class RevokeNodeView(MobileView):
    @transaction.atomic
    def post(self, request, node_id):
        node = get_object_or_404(DetectionNode, pk=node_id)
        acting(request.user, node.patient_id, "manage_nodes")
        node.active = False
        node.save(update_fields=["active"])
        return JsonResponse({"revoked": True})


class ObservationsView(MobileView):
    def get(self, request, pk):
        p, _ = patient_for(request.user, pk, "detection")
        page = max(1, int(request.GET.get("page", 1)))
        rows = list(
            PostureObservation.objects.filter(Q(node__patient=p) | Q(phone_patient=p)).select_related("node")[
                (page - 1) * 30 : page * 30 + 1
            ]
        )
        return JsonResponse(
            {
                "items": [
                    {
                        "id": r.pk,
                        "posture": r.posture,
                        "confidence": r.confidence,
                        "observed_at": r.observed_at,
                        "received_at": r.received_at,
                        "risk": r.risk,
                        "source": r.node.name if r.node_id else f"Teléfono {r.platform}",
                        "source_type": "fixed" if r.node_id else "phone",
                        "model_version": r.model_version,
                        "rule_version": r.rule_version,
                    }
                    for r in rows[:30]
                ],
                "next_page": page + 1 if len(rows) > 30 else None,
                "enabled": capabilities(p.owner)["features"]["posture_detection"],
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class EdgeView(View):
    http_method_names = ["get", "post"]

    def dispatch(self, request, *args, **kwargs):
        response = self.handle(request)
        response["Cache-Control"] = "no-store, private"
        return response

    def handle(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer ") or len(header) > 128:
            return error("Nodo no autorizado.", 401)
        hashed = hashlib.sha256(header[7:].encode()).hexdigest()
        node = (
            DetectionNode.objects.select_related("patient__owner")
            .filter(credential_hash=hashed, active=True)
            .first()
        )
        if not node:
            return error("Nodo no autorizado.", 401)
        try:
            with transaction.atomic():
                user = locked_user(node.patient.owner)
                # Lock order matches commercial transitions; re-check revocation.
                node = DetectionNode.objects.select_for_update().get(pk=node.pk)
                if not node.active:
                    raise PermissionDenied
                allowed(user, node.patient)
                if request.method == "GET":
                    state, now = monitor_state_param(request), timezone.now()
                    fields = {"last_seen_at": now}
                    if state is not None and state != node.monitor_state:
                        fields.update(monitor_state=state, monitor_since=now)
                    DetectionNode.objects.filter(pk=node.pk).update(**fields)
                    return JsonResponse(
                        {
                            "enabled": True,
                            "lease_seconds": 30,
                            "server_time": timezone.now(),
                        }
                    )
                if (
                    request.content_type != "application/json"
                    or len(request.body) > 4096
                ):
                    return error("Envía metadatos JSON de hasta 4 KB.")
                d = json.loads(request.body)
                required = {
                    "event_id",
                    "observed_at",
                    "posture",
                    "confidence",
                    "model_version",
                    "rule_version",
                    "risk",
                }
                if not isinstance(d, dict) or set(d) != required:
                    return error(
                        "Contrato de observación inválido; no se aceptan imágenes ni coordenadas."
                    )
                event_id = uuid.UUID(d["event_id"])
                observed = parse_datetime(d["observed_at"])
                if observed is None or timezone.is_naive(observed):
                    return error("La observación debe incluir zona horaria.")
                # A risk event may arrive late after the node reconnects; it
                # keeps its original time and its event_id deduplicates retries.
                max_age = RISK_MAX_AGE if d["risk"] else timedelta(minutes=2)
                if (
                    not timezone.now() - max_age
                    <= observed
                    <= timezone.now() + timedelta(seconds=30)
                ):
                    return error("Observación vencida o reloj incorrecto.")
                confidence = float(d["confidence"])
                if (
                    isinstance(d["confidence"], bool)
                    or not math.isfinite(confidence)
                    or not 0 <= confidence <= 1
                ):
                    return error("Confianza inválida.")
                if d["posture"] not in (
                    "supina",
                    "lateral-izquierda",
                    "lateral-derecha",
                    "indeterminada",
                ):
                    return error("Postura inválida.")
                # A person on the floor rarely matches the bed calibration, so a
                # fall may arrive as "indeterminada"; immobility may not.
                if d["risk"] not in ("", "immobility", "fall") or (
                    d["posture"] == "indeterminada" and d["risk"] == "immobility"
                ):
                    return error("Riesgo inválido para esta observación.")
                if any(
                    not isinstance(d[k], str) or not 1 <= len(d[k]) <= 80
                    for k in ("model_version", "rule_version")
                ):
                    return error("Versión inválida.")
                previous = PostureObservation.objects.filter(
                    node=node, event_id=event_id
                ).first()
                payload = digest(d)
                if previous:
                    return (
                        JsonResponse({"id": previous.pk, "duplicate": True})
                        if previous.payload_hash == payload
                        else error("Evento reutilizado con otros datos.", 409)
                    )
                row = PostureObservation.objects.create(
                    node=node,
                    event_id=event_id,
                    observed_at=observed,
                    posture=d["posture"],
                    confidence=confidence,
                    model_version=d["model_version"],
                    rule_version=d["rule_version"],
                    risk=d["risk"],
                    payload_hash=payload,
                )
                DetectionNode.objects.filter(pk=node.pk).update(
                    last_seen_at=timezone.now()
                )
                if row.risk == "fall":
                    # D-051: push right after commit, off the node's response path.
                    transaction.on_commit(lambda pk=row.pk: push.schedule_fall(pk))
                if row.risk:
                    # Reception time for the alert-latency KPI; no patient data.
                    log.warning(
                        "Riesgo %s recibido: observación=%s event_id=%s observed_at=%s received_at=%s retraso=%.3f s",
                        row.risk,
                        row.pk,
                        row.event_id,
                        row.observed_at.isoformat(),
                        row.received_at.isoformat(),
                        (row.received_at - row.observed_at).total_seconds(),
                    )
                return JsonResponse({"id": row.pk, "duplicate": False}, status=201)
        except PermissionDenied:
            return error(
                "Monitoreo no activo: revisa plan, paciente o revocación.", 403
            )
        except (ValueError, TypeError, KeyError, ValidationError):
            return error("Revisa los metadatos de la observación.")


class PhoneObservationsView(MobileView):
    """Session-authenticated snapshots, never continuous-risk events or node credentials."""
    def get(self, request, pk):
        patient, _ = patient_for(request.user, pk, "record")
        allowed(request.user, patient)
        return JsonResponse({"enabled": True, "mode": "snapshot", "server_time": timezone.now()})

    @transaction.atomic
    def post(self, request, pk):
        user, _, patient, _ = acting(request.user, pk, "record")
        allowed(user, patient)
        data = self.data
        required = {"event_id", "observed_at", "posture", "confidence", "platform", "model_version", "rule_version"}
        if set(data) != required or len(request.body) > 4096:
            raise ValidationError("Solo se admiten metadatos de observación, sin imagen ni coordenadas.")
        event_id = uuid.UUID(data["event_id"])
        observed = parse_datetime(data["observed_at"])
        if observed is None or timezone.is_naive(observed):
            raise ValidationError("La fecha debe incluir zona horaria.")
        if not timezone.now() - timedelta(minutes=2) <= observed <= timezone.now() + timedelta(seconds=30):
            raise ValidationError("Observación vencida; realiza otro análisis.")
        confidence = float(data["confidence"])
        if isinstance(data["confidence"], bool) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValidationError("Similitud inválida.")
        if data["posture"] not in ("supina", "lateral-izquierda", "lateral-derecha", "indeterminada"):
            raise ValidationError("Postura inválida.")
        if data["platform"] not in ("android", "ios"):
            raise ValidationError("Plataforma inválida.")
        if any(not isinstance(data[k], str) or not 1 <= len(data[k]) <= 80 for k in ("model_version", "rule_version")):
            raise ValidationError("Versión inválida.")
        payload_hash = digest(data)
        previous = PostureObservation.objects.filter(phone_patient=patient, event_id=event_id).first()
        if previous:
            return (JsonResponse({"id": previous.pk, "duplicate": True}) if previous.payload_hash == payload_hash
                    else error("Evento reutilizado con otros datos.", 409))
        row = PostureObservation.objects.create(
            phone_patient=patient, platform=data["platform"], event_id=event_id,
            observed_at=observed, posture=data["posture"], confidence=confidence,
            model_version=data["model_version"], rule_version=data["rule_version"], payload_hash=payload_hash,
        )
        return JsonResponse({"id": row.pk, "duplicate": False, "source_type": "phone"}, status=201)
