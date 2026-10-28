"""Planes y suscripciones.

La colección `plans` es la fuente de verdad de límites y precios. `DEFAULT_PLANS` solo se usa
para cargarla la primera vez (script seed_plans); después se edita desde el portal (Fase 5).
"""

from fastapi import status
from google.cloud import firestore

from app.core.errors import AppError
from app.core.firebase import get_db

PLANS = "plans"
SUBSCRIPTIONS = "subscriptions"
DEFAULT_PLAN_ID = "free"

# Precios en CLP: VALORES DE PRUEBA, no comerciales (priceIsTest).
DEFAULT_PLANS: dict[str, dict] = {
    "free": {
        "name": "Gratis",
        "order": 1,
        "maxPatients": 1,
        "priceClp": 0,
        "priceIsTest": True,
        "available": True,
        "features": {
            "extendedCareTracking": False,
            "positionChanges": False,
            "historyDays": 30,
            "pdfReport": False,
            "cameras": False,
            "advancedAlerts": False,
        },
    },
    "plus": {
        "name": "Plus",
        "order": 2,
        "maxPatients": 3,
        "priceClp": 4990,
        "priceIsTest": True,
        "available": True,
        "features": {
            "extendedCareTracking": True,
            "positionChanges": True,
            "historyDays": 365,
            "pdfReport": True,
            "cameras": False,
            "advancedAlerts": False,
        },
    },
    "premium": {
        "name": "Premium",
        "order": 3,
        "maxPatients": None,  # sin límite
        "priceClp": 9990,
        "priceIsTest": True,
        "available": True,
        "features": {
            "extendedCareTracking": True,
            "positionChanges": True,
            "historyDays": None,  # completo
            "pdfReport": True,
            "cameras": True,
            "advancedAlerts": True,
        },
    },
}


def seed_plans(overwrite: bool = False) -> list[str]:
    """Carga los planes por defecto. Sin overwrite no toca planes ya existentes."""
    db = get_db()
    written = []
    for plan_id, data in DEFAULT_PLANS.items():
        ref = db.collection(PLANS).document(plan_id)
        if overwrite or not ref.get().exists:
            ref.set({**data, "updatedAt": firestore.SERVER_TIMESTAMP})
            written.append(plan_id)
    return written


def subscription_ref(uid: str) -> firestore.DocumentReference:
    return get_db().collection(SUBSCRIPTIONS).document(uid)


def new_subscription() -> dict:
    return {
        "planId": DEFAULT_PLAN_ID,
        "status": "active",
        "simulated": True,  # MVP: sin cobros reales
        "startedAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }


def read_plan_for_user(uid: str, transaction: firestore.Transaction | None = None) -> tuple[str, dict]:
    """Devuelve (plan_id, datos del plan) del usuario.

    Sin suscripción se aplica el plan Gratis, el más restrictivo (nunca concede de más).
    Si el plan no está cargado en Firestore, la operación se rechaza en vez de suponer límites.
    """
    db = get_db()
    sub = subscription_ref(uid).get(transaction=transaction)
    plan_id = (sub.get("planId") if sub.exists else None) or DEFAULT_PLAN_ID
    plan = db.collection(PLANS).document(plan_id).get(transaction=transaction)
    if not plan.exists:
        raise AppError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "plans_not_configured",
            "Los planes no están configurados. Contacta al soporte de VIGIA.",
        )
    return plan_id, plan.to_dict()
