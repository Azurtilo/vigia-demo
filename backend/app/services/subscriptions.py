"""Cambios de plan simulados.

- Subir de plan: inmediato.
- Bajar quedando sobre el nuevo límite: exige confirmación explícita; no se borra nada.
- El cambio y el alta de pacientes leen el mismo contador y la misma suscripción dentro de
  transacciones: nunca se crea un paciente por sobre el límite vigente en ese momento.
"""

from datetime import UTC, datetime
from typing import Literal

from fastapi import status
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.subscription import Plan, PlanChangePreview, PlanFeatures, Subscription, SubscriptionChange
from app.services import edge_cache, plans
from app.services import patients as patients_service
from app.services.audit import audit_entry, audit_ref

CHANGES = "subscriptionChanges"

_FEATURE_NAMES = {
    "extendedCareTracking": "seguimiento ampliado de tareas",
    "positionChanges": "registro de cambios de posición",
    "pdfReport": "informe PDF",
    "cameras": "cámaras y análisis de postura",
    "advancedAlerts": "alertas avanzadas",
}


def to_plan(plan_id: str, d: dict) -> Plan:
    f = d.get("features", {})
    return Plan(
        id=plan_id,
        name=d["name"],
        order=d.get("order", 0),
        max_patients=d.get("maxPatients"),
        price_clp=d.get("priceClp", 0),
        price_is_test=d.get("priceIsTest", True),
        available=d.get("available", True),
        features=PlanFeatures(
            extended_care_tracking=f.get("extendedCareTracking", False),
            position_changes=f.get("positionChanges", False),
            history_days=f.get("historyDays"),
            pdf_report=f.get("pdfReport", False),
            cameras=f.get("cameras", False),
            advanced_alerts=f.get("advancedAlerts", False),
        ),
    )


def list_plans(include_unavailable: bool = False) -> list[Plan]:
    all_plans = [to_plan(s.id, s.to_dict()) for s in get_db().collection(plans.PLANS).stream()]
    return sorted([p for p in all_plans if include_unavailable or p.available], key=lambda p: p.order)


def _lost_features(current: dict, target: dict) -> list[str]:
    cf, tf = current.get("features", {}), target.get("features", {})
    lost = [name for key, name in _FEATURE_NAMES.items() if cf.get(key) and not tf.get(key)]
    c_days, t_days = cf.get("historyDays"), tf.get("historyDays")
    if t_days is not None and (c_days is None or t_days < c_days):
        lost.append(f"historial visible limitado a {t_days} días")
    return lost


def _over_limit(target: dict, active: int) -> bool:
    return target.get("maxPatients") is not None and active > target["maxPatients"]


def _over_limit_message(target: dict, active: int) -> str:
    return (
        f"Tienes {active} pacientes activos y el plan {target['name']} permite {target['maxPatients']}. "
        "No se borrará nada, pero no podrás agregar ni reactivar pacientes hasta archivar los necesarios."
    )


def _read_target(plan_id: str, transaction=None) -> dict:
    snap = get_db().collection(plans.PLANS).document(plan_id).get(transaction=transaction)
    if not snap.exists:
        raise AppError(status.HTTP_404_NOT_FOUND, "plan_not_found", "Ese plan no existe.")
    return snap.to_dict()


def _active_patients(uid: str, transaction=None) -> int:
    user = get_db().collection("users").document(uid).get(transaction=transaction)
    return (user.get("activePatientCount") or 0) if user.exists else 0


# ---------- Consultas ----------


def subscription(uid: str) -> Subscription:
    plan_id, plan = plans.read_plan_for_user(uid)
    sub = plans.subscription_ref(uid).get()
    changes = (
        get_db()
        .collection(CHANGES)
        .where(filter=FieldFilter("uid", "==", uid))
        .order_by("at", direction=firestore.Query.DESCENDING)
        .limit(10)
        .stream()
    )
    return Subscription(
        plan_id=plan_id,
        plan_name=plan["name"],
        status="active",
        simulated=True,
        started_at=sub.get("startedAt") if sub.exists else None,
        usage=patients_service.plan_usage(uid),
        recent_changes=[_to_change(c.id, c.to_dict()) for c in changes],
    )


def _to_change(change_id: str, d: dict) -> SubscriptionChange:
    return SubscriptionChange(
        id=change_id,
        from_plan=d.get("fromPlan"),
        to_plan=d["toPlan"],
        changed_by=d["changedBy"],
        actor_role=d["actorRole"],
        price_clp=d["priceClp"],
        price_is_test=d["priceIsTest"],
        over_limit_confirmed=d.get("overLimitConfirmed", False),
        at=d.get("at"),
    )


def preview(uid: str, plan_id: str) -> PlanChangePreview:
    current_id, current = plans.read_plan_for_user(uid)
    target = _read_target(plan_id)
    active = _active_patients(uid)
    over = _over_limit(target, active)
    lost = _lost_features(current, target)
    if plan_id == current_id:
        message = "Ya tienes este plan."
    elif over:
        message = _over_limit_message(target, active)
    elif lost:
        message = "Dejarás de tener: " + ", ".join(lost) + ". No se borrará ningún dato."
    else:
        message = "Puedes cambiarte a este plan sin restricciones."
    return PlanChangePreview(
        current_plan_id=current_id,
        target=to_plan(plan_id, target),
        active_patients=active,
        over_limit=over,
        lost_features=lost,
        requires_confirmation=over and plan_id != current_id,
        message=message,
    )


# ---------- Cambio ----------


def change_plan(
    uid: str,
    plan_id: str,
    confirm_over_limit: bool,
    actor_uid: str,
    actor_role: Literal["user", "admin"],
) -> Subscription:
    db = get_db()
    sub_ref = plans.subscription_ref(uid)
    change_ref = db.collection(CHANGES).document()

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> None:
        if not db.collection("users").document(uid).get(transaction=transaction).exists:
            raise AppError(status.HTTP_404_NOT_FOUND, "user_not_found", "El usuario no existe.")
        sub = sub_ref.get(transaction=transaction)
        current_id = (sub.get("planId") if sub.exists else None) or plans.DEFAULT_PLAN_ID
        target = _read_target(plan_id, transaction)
        active = _active_patients(uid, transaction)
        if plan_id == current_id:
            raise AppError(status.HTTP_409_CONFLICT, "already_on_plan", "Ya tienes este plan.")
        if not target.get("available", True) and actor_role != "admin":
            raise AppError(status.HTTP_409_CONFLICT, "plan_unavailable", "Este plan no está disponible por ahora.")
        over = _over_limit(target, active)
        if over and not confirm_over_limit:
            raise AppError(status.HTTP_409_CONFLICT, "downgrade_over_limit", _over_limit_message(target, active))
        transaction.set(
            sub_ref,
            {
                "planId": plan_id,
                "status": "active",
                "simulated": True,
                "startedAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
        transaction.set(
            change_ref,
            {
                "uid": uid,
                "fromPlan": current_id if sub.exists else None,
                "toPlan": plan_id,
                "changedBy": actor_uid,
                "actorRole": actor_role,
                "priceClp": target.get("priceClp", 0),
                "priceIsTest": target.get("priceIsTest", True),
                "overLimitConfirmed": over,
                "simulated": True,
                "at": datetime.now(UTC),
            },
        )
        transaction.set(
            audit_ref(),
            audit_entry(
                actor_uid,
                "subscription.changed",
                f"users/{uid}",
                {"from": current_id, "to": plan_id, "actorRole": actor_role, "overLimitConfirmed": over},
            ),
        )

    patients_service.run_transaction(_apply)
    edge_cache.forget(owner_uid=uid)  # el plan del dueño decide si sus nodos pueden capturar
    return subscription(uid)
