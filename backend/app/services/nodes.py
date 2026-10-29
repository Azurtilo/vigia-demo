"""Nodos de detección, contrato Edge y observaciones (RF-019-02, 03, 05, 10, 11).

El contrato Edge es el mismo de la API Django (specs 010, 012 y 017), así el nodo no cambia:
- el cuerpo se valida a mano y un error responde 400, que el nodo trata como definitivo
  (un 422 lo haría reintentar);
- 401 sin token válido y 403 si el monitoreo no está activo detienen la captura en el nodo.
"""

import hashlib
import json
import logging
import math
import secrets
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import partial

from fastapi import status
from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.nodes import CameraState, Node, NodeCreated, NodeList, Observation, ObservationPage
from app.services import alerts, consent, edge_cache, plans
from app.services.audit import audit_entry, audit_ref
from app.services.care_common import owner_features, require_active_patient, require_feature
from app.services.patients import PATIENTS, Access, get_access, run_transaction

log = logging.getLogger("vigia.edge")

NODES = "edgeNodes"
LEASE_SECONDS = 30
CONNECTED_FOR = timedelta(seconds=90)
SEEN_WRITE_SECONDS = 30
MAX_BODY = 4096
# Un evento de riesgo puede llegar tarde tras una reconexión: conserva su hora original (el nodo
# deja de reintentar a los 55 min). Las observaciones comunes vencen a los 2 minutos.
RISK_MAX_AGE = timedelta(hours=1)
OBSERVATION_MAX_AGE = timedelta(minutes=2)
FUTURE_TOLERANCE = timedelta(seconds=30)
MONITOR_STATES = {"normal", "persona_no_visible", "sin_imagen", "poca_luz"}
POSTURES = {"supina", "lateral-izquierda", "lateral-derecha", "indeterminada"}
# D-077: con varios nodos se muestra el peor estado.
CAMERA_PRIORITY = ["sin_senal", "sin_imagen", "poca_luz", "persona_no_visible", "normal"]
EDGE_KEYS = {"event_id", "observed_at", "posture", "confidence", "model_version", "rule_version", "risk"}
PHONE_KEYS = {"event_id", "observed_at", "posture", "confidence", "platform", "model_version", "rule_version"}
PAGE_SIZE = 30


def utcnow() -> datetime:
    return datetime.now(UTC)


def _bad(message: str) -> AppError:
    return AppError(status.HTTP_400_BAD_REQUEST, "invalid_observation", message)


def _unauthorized() -> AppError:
    return AppError(status.HTTP_401_UNAUTHORIZED, "node_unauthorized", "Nodo no autorizado.")


def _inactive() -> AppError:
    return AppError(
        status.HTTP_403_FORBIDDEN, "monitoring_inactive", "Monitoreo no activo: revisa plan, paciente o revocación."
    )


def _owner_only(access: Access) -> None:
    if access.relation != "owner":
        raise AppError(status.HTTP_403_FORBIDDEN, "owner_only", "Solo el responsable del paciente puede hacer esto.")


def _require_detection(access: Access) -> None:
    """Cámara en el plan del dueño y consentimiento de detección (falla cerrado)."""
    require_feature(access, "cameras", "La detección con cámara")
    if not consent.is_active(access.patient_id, "deteccion"):
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "consent_required",
            "Registra el consentimiento de detección con cámara de este paciente antes de usarla.",
        )


def digest(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def credential_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def observations(patient_id: str) -> firestore.CollectionReference:
    return get_db().collection(PATIENTS).document(patient_id).collection("observations")


# ---------- Gestión de nodos (solo el dueño) ----------


def _connected(d: dict, node_id: str) -> tuple[bool, datetime | None]:
    seen = max(
        (t for t in (d.get("lastSeenAt"), edge_cache.last_seen(node_id)) if t is not None),
        default=None,
    )
    return bool(d.get("active") and seen and seen > utcnow() - CONNECTED_FOR), seen


def _to_node(node_id: str, d: dict) -> Node:
    connected, seen = _connected(d, node_id)
    return Node(
        id=node_id,
        name=d["name"],
        active=d["active"],
        last_seen_at=seen,
        connected=connected,
        monitor_state=d.get("monitorState") or "desconocido",
        monitor_since=d.get("monitorSince"),
    )


def _patient_nodes(patient_id: str) -> list[tuple[str, dict]]:
    query = get_db().collection(NODES).where(filter=FieldFilter("patientId", "==", patient_id))
    rows = [(s.id, s.to_dict()) for s in query.stream()]
    return sorted(rows, key=lambda r: r[1].get("createdAt") or utcnow(), reverse=True)


def list_nodes(patient_id: str, uid: str) -> NodeList:
    _owner_only(get_access(patient_id, uid))
    return NodeList(items=[_to_node(i, d) for i, d in _patient_nodes(patient_id)])


def link_node(patient_id: str, uid: str, name: str) -> NodeCreated:
    access = get_access(patient_id, uid)
    _owner_only(access)
    require_active_patient(access)
    _require_detection(access)
    token = secrets.token_urlsafe(32)
    db = get_db()
    node_ref = db.collection(NODES).document()
    patient_ref = db.collection(PATIENTS).document(patient_id)
    data = {
        "patientId": patient_id,
        "ownerUid": access.patient["ownerUid"],
        "name": name,
        "credentialHash": credential_hash(token),
        "active": True,
        "createdBy": uid,
        "createdAt": utcnow(),
        "lastSeenAt": None,
        "monitorState": None,
        "monitorSince": None,
    }

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        # Una cámara activa por paciente: límite técnico explícito del piloto.
        if (patient_ref.get(transaction=transaction).to_dict() or {}).get("activeNodeId"):
            raise AppError(
                status.HTTP_409_CONFLICT, "node_already_active", "Revoca el nodo anterior antes de vincular otro."
            )
        transaction.set(node_ref, data)
        transaction.update(patient_ref, {"activeNodeId": node_ref.id})
        transaction.set(audit_ref(), audit_entry(uid, "node.linked", f"{NODES}/{node_ref.id}"))

    run_transaction(_apply)
    return NodeCreated(**_to_node(node_ref.id, data).model_dump(), credential=token)


def revoke_node(node_id: str, uid: str) -> dict:
    db = get_db()
    node_ref = db.collection(NODES).document(node_id)
    snapshot = node_ref.get()
    if not snapshot.exists:
        raise AppError(status.HTTP_404_NOT_FOUND, "node_not_found", "Nodo no encontrado.")
    patient_id = snapshot.get("patientId")
    _owner_only(get_access(patient_id, uid))
    patient_ref = db.collection(PATIENTS).document(patient_id)

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        active_id = (patient_ref.get(transaction=transaction).to_dict() or {}).get("activeNodeId")
        transaction.update(node_ref, {"active": False, "revokedAt": utcnow(), "revokedBy": uid})
        if active_id == node_id:
            transaction.update(patient_ref, {"activeNodeId": firestore.DELETE_FIELD})
        transaction.set(audit_ref(), audit_entry(uid, "node.revoked", f"{NODES}/{node_id}"))

    run_transaction(_apply)
    edge_cache.forget(patient_id=patient_id)
    return {"revoked": True}


def camera_state(patient_id: str, uid: str) -> CameraState:
    """Estado agregado de solo lectura para todos los miembros, sin datos del nodo (D-077)."""
    access = get_access(patient_id, uid, "patient.view")
    if not owner_features(access).get("cameras"):
        return CameraState(state=None)
    states = set()
    for node_id, d in _patient_nodes(patient_id):
        if d.get("active"):
            connected, _ = _connected(d, node_id)
            states.add((d.get("monitorState") or "desconocido") if connected else "sin_senal")
    return CameraState(state=next((s for s in CAMERA_PRIORITY if s in states), None))


# ---------- Contrato Edge ----------


def _load(h: str) -> edge_cache.NodeAuth | None:
    db = get_db()
    # Solo igualdad sobre el hash (índice simple automático); `active` se revisa aquí.
    found = next(iter(db.collection(NODES).where(filter=FieldFilter("credentialHash", "==", h)).limit(1).stream()), None)
    if found is None or not found.get("active"):
        return None
    d = found.to_dict()
    patient = db.collection(PATIENTS).document(d["patientId"]).get()
    allowed = False
    if patient.exists and patient.get("status") == "active":
        owner_uid = patient.get("ownerUid")
        _, plan = plans.read_plan_for_user(owner_uid)
        allowed = bool(plan.get("features", {}).get("cameras")) and consent.is_active(d["patientId"], "deteccion")
    return edge_cache.NodeAuth(
        node_id=found.id,
        patient_id=d["patientId"],
        owner_uid=d["ownerUid"],
        node_name=d["name"],
        allowed=allowed,
        checked_at=edge_cache.clock(),
        monitor_state=d.get("monitorState"),
    )


def authorize(header: str) -> edge_cache.NodeAuth:
    if not header.startswith("Bearer ") or len(header) > 128:
        raise _unauthorized()
    h = credential_hash(header[7:])
    entry = edge_cache.fresh(h)
    if entry is None:
        generation = edge_cache.generation()
        loaded = _load(h)
        if loaded is None:
            edge_cache.drop(h)
            raise _unauthorized()
        old = edge_cache.previous(h)
        if old is not None and old.node_id == loaded.node_id:
            # Lo que aún no se escribió en Firestore vive en memoria: se conserva.
            loaded.monitor_state = old.monitor_state
            loaded.last_seen, loaded.seen_written_at = old.last_seen, old.seen_written_at
        edge_cache.store(h, loaded, generation)
        entry = loaded
    if not entry.allowed:
        raise _inactive()
    return entry


def _write_node(node_id: str, changes: dict) -> None:
    get_db().collection(NODES).document(node_id).update(changes)


def _touch(entry: edge_cache.NodeAuth, state: str | None) -> None:
    """Última señal en memoria; en Firestore solo si cambió el estado o pasaron 30 s."""
    now, tick = utcnow(), edge_cache.clock()
    changes: dict = {}
    with edge_cache.lock():
        entry.last_seen = now
        if state is not None and state != entry.monitor_state:
            entry.monitor_state = state
            changes |= {"monitorState": state, "monitorSince": now}
        if changes or tick - entry.seen_written_at >= SEEN_WRITE_SECONDS:
            entry.seen_written_at = tick
            changes["lastSeenAt"] = now
    if changes:
        _write_node(entry.node_id, changes)


def edge_status(header: str, query: list[tuple[str, str]]) -> dict:
    """Renovación del nodo (`GET /api/v1/edge/status`), con `monitor_state` opcional (D-073)."""
    entry = authorize(header)
    if {key for key, _ in query} - {"monitor_state"}:
        raise _bad("Parámetro no admitido en la renovación del nodo.")
    values = [value for key, value in query if key == "monitor_state"]
    if len(values) > 1 or (values and values[0] not in MONITOR_STATES):
        raise _bad("Estado de monitoreo inválido.")
    _touch(entry, values[0] if values else None)
    return {"enabled": True, "lease_seconds": LEASE_SECONDS, "server_time": utcnow().isoformat()}


def _parse(body: bytes):
    try:
        return json.loads(body)
    except (ValueError, UnicodeDecodeError):
        raise _bad("Revisa los metadatos de la observación.")


def _validate(d: dict, *, max_age: timedelta, stale: str, confidence_label: str) -> dict:
    """Mismas reglas y orden que la API Django. Devuelve los valores normalizados."""
    try:
        event_id = uuid.UUID(d["event_id"])
        observed = datetime.fromisoformat(d["observed_at"])
        if observed.tzinfo is None:
            raise _bad("La observación debe incluir zona horaria.")
        now = utcnow()
        if not now - max_age <= observed <= now + FUTURE_TOLERANCE:
            raise _bad(stale)
        confidence = float(d["confidence"])
        if isinstance(d["confidence"], bool) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise _bad(confidence_label)
        if d["posture"] not in POSTURES:
            raise _bad("Postura inválida.")
        if any(not isinstance(d[k], str) or not 1 <= len(d[k]) <= 80 for k in ("model_version", "rule_version")):
            raise _bad("Versión inválida.")
    except (ValueError, TypeError, KeyError, AttributeError):
        raise _bad("Revisa los metadatos de la observación.")
    return {
        "eventId": str(event_id),
        "observedAt": observed.astimezone(UTC),
        "posture": d["posture"],
        "confidence": confidence,
        "modelVersion": d["model_version"],
        "ruleVersion": d["rule_version"],
    }


def _store(patient_id: str, doc_id: str, record: dict, alert: tuple[str, dict] | None = None) -> tuple[int, dict]:
    """Guarda la observación y, si tiene riesgo, su alerta en el mismo lote."""
    ref = observations(patient_id).document(doc_id)
    batch = get_db().batch()
    batch.create(ref, record)
    if alert is not None:
        batch.create(alerts.alerts_of(patient_id).document(alert[0]), alert[1])
    try:
        batch.commit()
    except AlreadyExists:
        # El mismo event_id con el mismo contenido es un reintento; con otro contenido, un error.
        if ref.get().get("payloadHash") == record["payloadHash"]:
            return status.HTTP_200_OK, {"id": doc_id, "duplicate": True}
        raise AppError(status.HTTP_409_CONFLICT, "event_reused", "Evento reutilizado con otros datos.")
    return status.HTTP_201_CREATED, {"id": doc_id, "duplicate": False}


def edge_observation(
    header: str, content_type: str, body: bytes | None
) -> tuple[int, dict, Callable[[], None] | None]:
    """Observación del nodo (`POST /api/v1/edge/observations`): exactamente 7 claves.

    Devuelve además, para una caída nueva, el envío del push a ejecutar después de responder.
    """
    entry = authorize(header)
    if content_type.split(";")[0].strip().lower() != "application/json" or body is None or len(body) > MAX_BODY:
        raise _bad("Envía metadatos JSON de hasta 4 KB.")
    d = _parse(body)
    if not isinstance(d, dict) or set(d) != EDGE_KEYS:
        raise _bad("Contrato de observación inválido; no se aceptan imágenes ni coordenadas.")
    values = _validate(
        d,
        max_age=RISK_MAX_AGE if d["risk"] else OBSERVATION_MAX_AGE,
        stale="Observación vencida o reloj incorrecto.",
        confidence_label="Confianza inválida.",
    )
    # Una persona en el suelo rara vez calza con la calibración de la cama: una caída puede llegar
    # como "indeterminada"; la inmovilidad no.
    if not isinstance(d["risk"], str) or d["risk"] not in ("", "immobility", "fall") or (
        d["posture"] == "indeterminada" and d["risk"] == "immobility"
    ):
        raise _bad("Riesgo inválido para esta observación.")
    received = utcnow()
    record = {
        **values,
        "risk": d["risk"],
        "sourceType": "fixed",
        "nodeId": entry.node_id,
        "nodeName": entry.node_name,
        "receivedAt": received,
        "payloadHash": digest(d),
    }
    doc_id = f"{entry.node_id}_{values['eventId']}"
    alert = alerts.observation_alert(doc_id, d["risk"], values["observedAt"], entry.node_id) if d["risk"] else None
    code, result = _store(entry.patient_id, doc_id, record, alert)
    _touch(entry, None)
    followup = None
    if code == status.HTTP_201_CREATED and d["risk"] == "fall":
        followup = partial(alerts.push_fall_now, entry.patient_id, alert[0])
    if code == status.HTTP_201_CREATED and d["risk"]:
        # Hora de recepción para medir la demora de la alerta; sin datos del paciente.
        log.warning(
            "Riesgo %s recibido: observación=%s observed_at=%s received_at=%s retraso=%.3f s",
            d["risk"],
            result["id"],
            values["observedAt"].isoformat(),
            received.isoformat(),
            (received - values["observedAt"]).total_seconds(),
        )
    return code, result, followup


# ---------- Cámara del teléfono y consulta ----------


def phone_status(patient_id: str, uid: str) -> dict:
    access = get_access(patient_id, uid, "care.record")
    require_active_patient(access)
    _require_detection(access)
    return {"enabled": True, "mode": "snapshot", "server_time": utcnow().isoformat()}


def phone_observation(patient_id: str, uid: str, body: bytes | None) -> tuple[int, dict]:
    """Análisis puntual con la cámara del teléfono: metadatos sin imagen ni riesgo continuo."""
    access = get_access(patient_id, uid, "care.record")
    require_active_patient(access)
    _require_detection(access)
    if body is None or len(body) > MAX_BODY:  # se revisa antes de parsear (QA-2026-10-28-02)
        raise _bad("Solo se admiten metadatos de observación, sin imagen ni coordenadas.")
    d = _parse(body)
    if not isinstance(d, dict) or set(d) != PHONE_KEYS:
        raise _bad("Solo se admiten metadatos de observación, sin imagen ni coordenadas.")
    values = _validate(
        d,
        max_age=OBSERVATION_MAX_AGE,
        stale="Observación vencida; realiza otro análisis.",
        confidence_label="Similitud inválida.",
    )
    if d["platform"] not in ("android", "ios"):
        raise _bad("Plataforma inválida.")
    record = {
        **values,
        "risk": "",
        "sourceType": "phone",
        "platform": d["platform"],
        "recordedBy": uid,
        "receivedAt": utcnow(),
        "payloadHash": digest(d),
    }
    code, result = _store(patient_id, f"phone_{values['eventId']}", record)
    return code, {**result, "sourceType": "phone"}


def list_observations(patient_id: str, uid: str, cursor: str | None = None) -> ObservationPage:
    """Observaciones de la más reciente a la más antigua, de a 30. Requiere `alerts.handle`."""
    access = get_access(patient_id, uid, "alerts.handle")
    query = observations(patient_id).order_by("observedAt", direction=firestore.Query.DESCENDING)
    if cursor:
        start = observations(patient_id).document(cursor).get()
        if not start.exists:
            raise AppError(status.HTTP_400_BAD_REQUEST, "invalid_cursor", "La página pedida no es válida.")
        query = query.start_after(start)
    rows = list(query.limit(PAGE_SIZE + 1).stream())
    items = [
        Observation(
            id=row.id,
            posture=d["posture"],
            confidence=d["confidence"],
            observed_at=d["observedAt"],
            received_at=d["receivedAt"],
            risk=d["risk"],
            source=d["nodeName"] if d["sourceType"] == "fixed" else f"Teléfono {d['platform']}",
            source_type=d["sourceType"],
            model_version=d["modelVersion"],
            rule_version=d["ruleVersion"],
        )
        for row in rows[:PAGE_SIZE]
        for d in [row.to_dict()]
    ]
    return ObservationPage(
        items=items,
        next_cursor=rows[PAGE_SIZE - 1].id if len(rows) > PAGE_SIZE else None,
        enabled=bool(owner_features(access).get("cameras")),
    )
