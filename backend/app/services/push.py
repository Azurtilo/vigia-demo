"""Envío por Firebase Cloud Messaging con un recibo por dispositivo y aviso (spec 012, RF-019-04).

Cada (instalación, aviso) se reserva en una transacción corta antes de llamar a FCM (nunca
dentro de ella): el push inmediato de
una caída y el ciclo del cron nunca envían dos veces lo mismo. Si FCM falla, la reserva se
libera y el ciclo siguiente reintenta. Una reserva sin confirmar de más de 2 minutos se
considera abandonada (proceso caído) y se puede tomar de nuevo.
"""

import hashlib
import logging
from datetime import UTC, datetime, timedelta

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
from google.api_core.exceptions import Aborted
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.config import get_settings
from app.core.firebase import get_db, init_firebase

log = logging.getLogger("vigia.push")

DEVICES = "devices"
RECEIPTS = "pushReceipts"
# D-058: un texto genérico; la pantalla bloqueada nunca revela un evento de salud.
RISK_TEXT = "VIGIA: alerta de riesgo, abre la app."
# D-074: la cámara no puede vigilar; también genérico y nunca con prioridad alta.
MONITOR_TEXT = "VIGIA: revisa la cámara de monitoreo, abre la app."
RESERVATION_TTL = timedelta(minutes=2)


def build(token: str, body: str, high_priority: bool) -> messaging.Message:
    return messaging.Message(
        token=token,
        notification=messaging.Notification(title="VIGIA", body=body),
        android=messaging.AndroidConfig(
            priority="high" if high_priority else None,
            notification=messaging.AndroidNotification(visibility="private"),
        ),
    )


def transport(message: messaging.Message) -> None:
    """Único punto que habla con FCM (las pruebas lo reemplazan)."""
    init_firebase()
    messaging.send(message)


def enabled() -> bool:
    return get_settings().push_enabled


def _receipt_ref(installation_id: str, key: str) -> firestore.DocumentReference:
    receipt_id = hashlib.sha256(f"{installation_id}|{key}".encode()).hexdigest()
    return get_db().collection(RECEIPTS).document(receipt_id)


def _reserve(ref: firestore.DocumentReference, installation_id: str, uid: str, key: str) -> bool:
    now = datetime.now(UTC)

    @firestore.transactional
    def _take(transaction: firestore.Transaction) -> bool:
        current = ref.get(transaction=transaction)
        if current.exists and (current.get("confirmed") or current.get("reservedAt") > now - RESERVATION_TTL):
            return False  # ya enviado, o en curso en otro envío
        transaction.set(
            ref, {"installationId": installation_id, "uid": uid, "key": key, "confirmed": False, "reservedAt": now}
        )
        return True

    try:
        return _take(get_db().transaction())
    except (Aborted, ValueError):
        return False  # otro envío ganó la reserva; el ciclo siguiente revisa de nuevo


def deliver(device_id: str, device: dict, key: str, body: str, high_priority: bool = False) -> bool | None:
    """True si FCM lo aceptó ahora; None si ya estaba enviado o en curso; False si falló."""
    ref = _receipt_ref(device_id, key)
    if not _reserve(ref, device_id, device["uid"], key):
        return None
    try:
        transport(build(device["token"], body, high_priority))
    except messaging.UnregisteredError:
        # La app se desinstaló o el token cambió: el dispositivo deja de recibir.
        ref.delete()
        get_db().collection(DEVICES).document(device_id).update({"active": False, "token": ""})
        return False
    except (FirebaseError, ValueError) as exc:
        ref.delete()
        log.warning("Push no confirmado: %s", type(exc).__name__)
        return False
    ref.update({"confirmed": True, "sentAt": datetime.now(UTC)})
    return True


def active_devices(uids: list[str]) -> list[tuple[str, dict]]:
    """Dispositivos activos de esas personas (consultas `in` de hasta 30 valores)."""
    found = []
    for i in range(0, len(uids), 30):
        query = get_db().collection(DEVICES).where(filter=FieldFilter("uid", "in", uids[i : i + 30]))
        found += [(s.id, s.to_dict()) for s in query.stream() if s.get("active")]
    return found
