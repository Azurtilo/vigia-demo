"""Alertas de riesgo y de cámara y su envío por push (RF-019-04, RF-019-05, RF-019-14).

- Caída: la alerta se escribe en el mismo lote que la observación y el push sale enseguida,
  fuera de la respuesta al nodo (D-051).
- Inmovilidad: alerta inmediata; el push sale en el ciclo del cron, como en Django.
- Cámara ciega (persona no visible, sin imagen) o nodo sin señal por más de 60 s: una alerta por
  episodio, creada en el ciclo del cron (D-074, D-075). "poca_luz" solo se muestra en la app.
- Destinatarios: miembros con `alerts.handle` y cuenta activa, si el plan del dueño incluye
  alertas avanzadas (D-063). El texto es genérico (D-058).
- Una alerta queda pendiente de push hasta que todos sus dispositivos lo confirman o pasa 1 hora.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import status
from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.alerts import Alert, AlertPage
from app.services import consent, edge_cache, plans, push
from app.services.patients import MEMBERSHIPS, PATIENTS, USERS, get_access, run_transaction

log = logging.getLogger("vigia.alerts")

ALERTS = "alerts"
RISK_PUSH_MAX_AGE = timedelta(hours=1)
NODE_OFFLINE_AFTER = timedelta(seconds=60)
BLIND_STATES = ("persona_no_visible", "sin_imagen")
CAMERA_KINDS = ("camera_blind", "node_offline")
PAGE_SIZE = 30
ME_PER_PATIENT = 20
ME_LIMIT = 50


def utcnow() -> datetime:
    return datetime.now(UTC)


def alerts_of(patient_id: str) -> firestore.CollectionReference:
    return get_db().collection(PATIENTS).document(patient_id).collection(ALERTS)


def observation_alert(observation_id: str, risk: str, occurred_at: datetime, node_id: str) -> tuple[str, dict]:
    """Alerta de una observación con riesgo; su ID deriva de la observación (no se duplica)."""
    return f"obs_{observation_id}", {
        "kind": risk,
        "nodeId": node_id,
        "observationId": observation_id,
        "occurredAt": occurred_at,
        "createdAt": utcnow(),
        "status": "open",
        "pushPending": True,
        "highPriority": risk == "fall",
    }


# ---------- Envío ----------


def recipients(patient_id: str) -> list[str]:
    db = get_db()
    members = db.collection(MEMBERSHIPS).where(filter=FieldFilter("patientId", "==", patient_id)).stream()
    uids = [m.get("uid") for m in members if "alerts.handle" in (m.to_dict().get("permissions") or [])]
    users = db.get_all([db.collection(USERS).document(uid) for uid in uids]) if uids else []
    return [u.id for u in users if u.exists and u.get("status") == "active"]


def push_alert(patient_id: str, alert_id: str) -> None:
    """Envía el push de una alerta pendiente a cada dispositivo de sus destinatarios."""
    if not push.enabled():
        return  # queda pendiente; se envía si el push se activa dentro de la hora
    ref = alerts_of(patient_id).document(alert_id)
    snapshot = ref.get()
    if not snapshot.exists or not snapshot.get("pushPending"):
        return
    d = snapshot.to_dict()
    if d["createdAt"] < utcnow() - RISK_PUSH_MAX_AGE:
        ref.update({"pushPending": False, "pushOutcome": "expired"})
        return
    owner_uid = get_db().collection(PATIENTS).document(patient_id).get().get("ownerUid")
    _, plan = plans.read_plan_for_user(owner_uid)
    if not plan.get("features", {}).get("advancedAlerts"):
        ref.update({"pushPending": False, "pushOutcome": "not_in_plan"})
        return
    body = push.MONITOR_TEXT if d["kind"] in CAMERA_KINDS else push.RISK_TEXT
    failed = False
    for device_id, device in push.active_devices(recipients(patient_id)):
        sent = push.deliver(device_id, device, f"alert:{patient_id}/{alert_id}", body, d.get("highPriority", False))
        failed = failed or sent is False
    if not failed:
        ref.update({"pushPending": False, "pushOutcome": "sent"})


def push_fall_now(patient_id: str, alert_id: str) -> None:
    """Push inmediato de una caída; si falla, el ciclo del cron reintenta (la alerta sigue pendiente)."""
    try:
        push_alert(patient_id, alert_id)
    except Exception as exc:  # nunca debe afectar al nodo; el reintento es del ciclo
        log.warning("Push inmediato no confirmado: %s", type(exc).__name__)


# ---------- Ciclo del cron (lo llama /internal/tick, T-019-06) ----------


def _monitoring_allowed(patient_id: str) -> bool:
    patient = get_db().collection(PATIENTS).document(patient_id).get()
    if not patient.exists or patient.get("status") != "active":
        return False
    _, plan = plans.read_plan_for_user(patient.get("ownerUid"))
    return bool(plan.get("features", {}).get("cameras")) and consent.is_active(patient_id, "deteccion")


def _node_episode(node_id: str, d: dict, now: datetime) -> tuple[str, dict] | None:
    last = max((t for t in (d.get("lastSeenAt"), edge_cache.last_seen(node_id)) if t is not None), default=None)
    if last is None:
        return None  # nunca se conectó: no hay episodio que avisar
    if last < now - NODE_OFFLINE_AFTER:
        if d.get("lastSeenAt") != last:
            # La última señal real estaba solo en memoria: se fija para que el episodio sea el mismo
            # aunque el proceso se reinicie.
            get_db().collection("edgeNodes").document(node_id).update({"lastSeenAt": last})
        kind, since, state = "node_offline", last, None
    elif d.get("monitorState") in BLIND_STATES and d.get("monitorSince"):
        kind, since, state = "camera_blind", d["monitorSince"], d["monitorState"]
    else:
        return None
    if since < now - RISK_PUSH_MAX_AGE:
        return None  # un episodio antiguo no se anuncia
    episode = f"node_{node_id}_{state or 'offline'}_{int(since.timestamp() * 1000)}"
    return episode, {
        "kind": kind,
        "nodeId": node_id,
        "monitorState": state,
        "occurredAt": since,
        "createdAt": now,
        "status": "open",
        "pushPending": True,
        "highPriority": False,
    }


def check_nodes(now: datetime | None = None) -> int:
    """Crea una alerta por episodio de cámara ciega o nodo sin señal. Devuelve cuántas creó."""
    now = now or utcnow()
    created = 0
    for node in get_db().collection("edgeNodes").where(filter=FieldFilter("active", "==", True)).stream():
        d = node.to_dict()
        episode = _node_episode(node.id, d, now)
        if episode is None or not _monitoring_allowed(d["patientId"]):
            continue  # detenido a propósito (plan, consentimiento, archivo): no es una falla
        alert_id, data = episode
        try:
            alerts_of(d["patientId"]).document(alert_id).create(data)
            created += 1
        except AlreadyExists:
            pass
    return created


def send_pending() -> int:
    """Envía (o reintenta) los push pendientes de todas las alertas. Devuelve cuántas revisó."""
    if not push.enabled():
        return 0
    pending = get_db().collection_group(ALERTS).where(filter=FieldFilter("pushPending", "==", True)).stream()
    reviewed = 0
    for snapshot in pending:
        try:
            push_alert(snapshot.reference.parent.parent.id, snapshot.id)
        except Exception as exc:  # una alerta con problemas no detiene a las demás
            log.warning("Alerta no enviada en el ciclo: %s", type(exc).__name__)
        reviewed += 1
    return reviewed


def run_cycle(now: datetime | None = None) -> dict:
    return {"camera_alerts": check_nodes(now), "pending_reviewed": send_pending()}


# ---------- Consulta y atención ----------


def _to_alert(snapshot, patient_id: str, patient_name: str | None = None) -> Alert:
    d = snapshot.to_dict()
    return Alert(
        id=snapshot.id,
        patient_id=patient_id,
        patient_name=patient_name,
        kind=d["kind"],
        monitor_state=d.get("monitorState"),
        occurred_at=d["occurredAt"],
        status=d["status"],
        attended_by=d.get("attendedBy"),
        attended_at=d.get("attendedAt"),
    )


def _newest(patient_id: str):
    return alerts_of(patient_id).order_by("occurredAt", direction=firestore.Query.DESCENDING)


def list_alerts(patient_id: str, uid: str, cursor: str | None = None) -> AlertPage:
    """Alertas del paciente, de la más reciente a la más antigua. Requiere `alerts.handle`."""
    get_access(patient_id, uid, "alerts.handle")
    query = _newest(patient_id)
    if cursor:
        start = alerts_of(patient_id).document(cursor).get()
        if not start.exists:
            raise AppError(status.HTTP_400_BAD_REQUEST, "invalid_cursor", "La página pedida no es válida.")
        query = query.start_after(start)
    rows = list(query.limit(PAGE_SIZE + 1).stream())
    return AlertPage(
        items=[_to_alert(s, patient_id) for s in rows[:PAGE_SIZE]],
        next_cursor=rows[PAGE_SIZE - 1].id if len(rows) > PAGE_SIZE else None,
    )


def my_alerts(uid: str) -> AlertPage:
    """Últimas alertas de todos los pacientes en que la persona tiene `alerts.handle` (RF-019-14)."""
    db = get_db()
    memberships = db.collection(MEMBERSHIPS).where(filter=FieldFilter("uid", "==", uid)).stream()
    patient_ids = [m.get("patientId") for m in memberships if "alerts.handle" in (m.to_dict().get("permissions") or [])]
    names = {
        p.id: p.get("displayName")
        for p in (db.get_all([db.collection(PATIENTS).document(pid) for pid in patient_ids]) if patient_ids else [])
        if p.exists
    }
    items = [
        _to_alert(s, pid, names[pid]) for pid in names for s in _newest(pid).limit(ME_PER_PATIENT).stream()
    ]
    items.sort(key=lambda a: a.occurred_at, reverse=True)
    return AlertPage(items=items[:ME_LIMIT])


def attend(patient_id: str, alert_id: str, uid: str) -> Alert:
    get_access(patient_id, uid, "alerts.handle")
    ref = alerts_of(patient_id).document(alert_id)

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        snapshot = ref.get(transaction=transaction)
        if not snapshot.exists:
            raise AppError(status.HTTP_404_NOT_FOUND, "alert_not_found", "Alerta no encontrada.")
        if snapshot.get("status") == "attended":
            raise AppError(status.HTTP_409_CONFLICT, "alert_already_attended", "La alerta ya fue atendida.")
        transaction.update(ref, {"status": "attended", "attendedBy": uid, "attendedAt": utcnow()})

    run_transaction(_apply)
    return _to_alert(ref.get(), patient_id)
