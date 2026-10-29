"""Dispositivos que reciben push (RF-019-09). Mismas reglas que la API Django.

Una instalación pertenece a una sola cuenta: si otra persona ingresa en el mismo teléfono, la
app crea una instalación nueva; así nadie recibe los avisos de otra cuenta.
"""

from datetime import UTC, datetime

from fastapi import status
from google.cloud import firestore

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.alerts import DeviceRegistration, ReminderMode
from app.services import push
from app.services.patients import run_transaction


def _taken() -> AppError:
    return AppError(
        status.HTTP_400_BAD_REQUEST, "installation_taken", "Registra una nueva instalación para esta cuenta."
    )


def register(uid: str, body: DeviceRegistration) -> dict:
    ref = get_db().collection(push.DEVICES).document(str(body.installation_id))

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        current = ref.get(transaction=transaction)
        if current.exists and current.get("uid") != uid:
            if body.enabled:
                raise _taken()
            return  # desactivar una instalación ajena no hace nada
        if not body.enabled:
            if current.exists:
                transaction.update(ref, {"active": False, "token": "", "updatedAt": datetime.now(UTC)})
            return
        transaction.set(
            ref,
            {
                "uid": uid,
                "token": body.token,
                "platform": body.platform,
                "active": True,
                "localPostureReminders": body.local_posture_reminders,
                "updatedAt": datetime.now(UTC),
            },
        )

    run_transaction(_apply)
    if not body.enabled:
        return {"enabled": False}
    return {"enabled": True, "deliveryConfigured": push.enabled()}


def reminder_mode(uid: str, body: ReminderMode) -> dict:
    ref = get_db().collection(push.DEVICES).document(str(body.installation_id))
    snapshot = ref.get()
    if snapshot.exists and snapshot.get("uid") == uid:
        ref.update({"localPostureReminders": body.local_posture_reminders})
    return {"saved": True}
