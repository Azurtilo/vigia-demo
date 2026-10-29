"""Endpoints de administración. Todos exigen rol `admin` (verificado en el backend, no en la interfaz)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import require_admin
from app.models.admin import AdminSubscriptionPage, PlanUpdate
from app.models.subscription import Plan, PlanChangeRequest, PlanId, Subscription
from app.models.user import UserProfile
from app.services import admin_plans
from app.services import subscriptions as subscriptions_service

router = APIRouter(prefix="/admin", tags=["administración"])

Admin = Annotated[UserProfile, Depends(require_admin)]

_errors = {401: {"description": "Sin sesión"}, 403: {"description": "No es administrador (`forbidden`)"}}


@router.get("/plans", response_model=list[Plan], responses=_errors)
def list_plans(_: Admin) -> list[Plan]:
    """Todos los planes, incluidos los no disponibles."""
    return subscriptions_service.list_plans(include_unavailable=True)


@router.patch("/plans/{plan_id}", response_model=Plan, responses={**_errors, 409: {"description": "Regla del plan Gratis"}})
def update_plan(plan_id: PlanId, body: PlanUpdate, admin: Admin) -> Plan:
    """Edita nombre, precio de PRUEBA, límite de pacientes, funciones o disponibilidad. Queda auditado (antes/después)."""
    return admin_plans.update_plan(plan_id, admin.uid, body)


@router.get("/subscriptions", response_model=AdminSubscriptionPage, responses=_errors)
def list_subscriptions(
    _: Admin,
    plan_id: Annotated[PlanId | None, Query(alias="planId")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> AdminSubscriptionPage:
    return admin_plans.list_subscriptions(plan_id, limit, cursor)


@router.post("/users/{uid}/subscription", response_model=Subscription, responses={**_errors, 404: {"description": "Usuario o plan no existe"}})
def change_user_plan(uid: str, body: PlanChangeRequest, admin: Admin) -> Subscription:
    """Cambia el plan de una persona (p. ej. por soporte). Mismas reglas que el cambio propio; queda como hecho por admin."""
    return subscriptions_service.change_plan(uid, body.plan_id, body.confirm_over_limit, admin.uid, "admin")
