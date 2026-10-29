"""Administración de planes y suscripciones (solo rol admin; la verificación de rol está en la API).

Reglas:
- Siempre los mismos tres planes: se editan, no se crean ni eliminan.
- Gratis: precio $0 y siempre disponible (es el plan de toda cuenta nueva).
- `priceIsTest` permanece verdadero en el MVP.
- Bajar el límite o quitar funciones no borra datos de nadie: aplica como una baja de plan.
"""

import re

from fastapi import status
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.admin import AdminSubscriptionPage, AdminSubscriptionRow, PlanUpdate
from app.models.subscription import Plan
from app.services import edge_cache, plans
from app.services import patients as patients_service
from app.services.audit import audit_entry, audit_ref
from app.services.subscriptions import to_plan

_FEATURE_KEYS = {
    "extended_care_tracking": "extendedCareTracking",
    "position_changes": "positionChanges",
    "history_days": "historyDays",
    "pdf_report": "pdfReport",
    "cameras": "cameras",
    "advanced_alerts": "advancedAlerts",
}
_UID = re.compile(r"^[A-Za-z0-9]{1,128}$")


def update_plan(plan_id: str, admin_uid: str, body: PlanUpdate) -> Plan:
    sent = body.model_fields_set
    changes: dict = {}
    if "name" in sent:
        changes["name"] = body.name
    if "price_clp" in sent:
        changes["priceClp"] = body.price_clp
    if "max_patients" in sent:
        changes["maxPatients"] = body.max_patients  # None = sin límite
    if "available" in sent:
        changes["available"] = body.available
    if "features" in sent and body.features is not None:
        for field in body.features.model_fields_set:
            changes[f"features.{_FEATURE_KEYS[field]}"] = getattr(body.features, field)
    if any(changes.get(k, "") is None for k in ("name", "priceClp", "available")):
        raise AppError(status.HTTP_422_UNPROCESSABLE_CONTENT, "validation_error", "Nombre, precio y disponibilidad no pueden quedar vacíos.")
    for key, value in changes.items():
        if key.startswith("features.") and key != "features.historyDays" and value is None:
            raise AppError(status.HTTP_422_UNPROCESSABLE_CONTENT, "validation_error", "Las funciones deben ser verdadero o falso.")

    ref = get_db().collection(plans.PLANS).document(plan_id)

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        snap = ref.get(transaction=transaction)
        if not snap.exists:
            raise AppError(status.HTTP_404_NOT_FOUND, "plan_not_found", "Ese plan no existe.")
        current = snap.to_dict()
        if plan_id == plans.DEFAULT_PLAN_ID:
            if changes.get("priceClp", 0) != 0:
                raise AppError(status.HTTP_409_CONFLICT, "free_plan_price_fixed", "El plan Gratis siempre cuesta $0.")
            if changes.get("available") is False:
                raise AppError(status.HTTP_409_CONFLICT, "free_plan_always_available", "El plan Gratis siempre debe estar disponible.")
        if not changes:
            return
        # Antes/después solo de lo que cambió (precios y límites no son datos sensibles).
        before = {}
        for key in changes:
            if key.startswith("features."):
                before[key] = current.get("features", {}).get(key.split(".", 1)[1])
            else:
                before[key] = current.get(key)
        transaction.update(ref, {**changes, "updatedAt": firestore.SERVER_TIMESTAMP})
        transaction.set(
            audit_ref(),
            audit_entry(admin_uid, "plan.updated", f"plans/{plan_id}", {"before": before, "after": changes}),
        )

    patients_service.run_transaction(_apply)
    edge_cache.forget(everything=True)  # puede cambiar la función de cámaras de muchos nodos
    return to_plan(plan_id, ref.get().to_dict())


def list_subscriptions(plan_id: str | None, limit: int, cursor: str | None) -> AdminSubscriptionPage:
    """Suscripciones ordenadas por uid, paginadas. Incluye correo: el portal admin lo necesita para soporte."""
    db = get_db()
    query = db.collection(plans.SUBSCRIPTIONS)
    if plan_id:
        query = query.where(filter=FieldFilter("planId", "==", plan_id))
    query = query.order_by("__name__")
    if cursor:
        if not _UID.match(cursor):
            raise AppError(status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_cursor", "El cursor de página no es válido.")
        query = query.start_after({"__name__": db.collection(plans.SUBSCRIPTIONS).document(cursor)})
    docs = list(query.limit(limit + 1).stream())
    page, has_more = docs[:limit], len(docs) > limit
    users = {
        s.id: s.to_dict()
        for s in (db.get_all([db.collection("users").document(d.id) for d in page]) if page else [])
        if s.exists
    }
    items = [
        AdminSubscriptionRow(
            uid=d.id,
            email=users.get(d.id, {}).get("email"),
            display_name=users.get(d.id, {}).get("displayName"),
            plan_id=d.get("planId"),
            status=d.get("status"),
            started_at=d.get("startedAt"),
            active_patients=users.get(d.id, {}).get("activePatientCount", 0),
        )
        for d in page
    ]
    return AdminSubscriptionPage(items=items, next_cursor=page[-1].id if has_more else None)
