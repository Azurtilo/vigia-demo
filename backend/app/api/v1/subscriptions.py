"""Planes disponibles y suscripción propia (cambios de plan simulados: el MVP no cobra)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.models.subscription import Plan, PlanChangePreview, PlanChangeRequest, PlanId, Subscription
from app.models.user import UserProfile
from app.services import subscriptions as subscriptions_service

router = APIRouter(tags=["planes y suscripción"])

CurrentUser = Annotated[UserProfile, Depends(get_current_user)]

_errors = {401: {"description": "Sin sesión o sesión inválida"}, 403: {"description": "Cuenta suspendida o sin registrar"}}


@router.get("/plans", response_model=list[Plan], responses=_errors)
def list_plans(_: CurrentUser) -> list[Plan]:
    """Planes que se pueden elegir, con precios de PRUEBA (no comerciales) y funciones."""
    return subscriptions_service.list_plans()


@router.get("/me/subscription", response_model=Subscription, responses=_errors)
def my_subscription(user: CurrentUser) -> Subscription:
    """Plan actual, uso y últimos 10 cambios."""
    return subscriptions_service.subscription(user.uid)


@router.get("/me/subscription/preview", response_model=PlanChangePreview, responses=_errors)
def preview_change(user: CurrentUser, plan_id: Annotated[PlanId, Query(alias="planId")]) -> PlanChangePreview:
    """Simula un cambio de plan SIN aplicarlo: precio, límite, funciones que se perderían."""
    return subscriptions_service.preview(user.uid, plan_id)


@router.post(
    "/me/subscription/change",
    response_model=Subscription,
    responses={
        **_errors,
        409: {"description": "`already_on_plan`, `plan_unavailable` o `downgrade_over_limit` (falta `confirmOverLimit`)"},
    },
)
def change_plan(body: PlanChangeRequest, user: CurrentUser) -> Subscription:
    """Cambia de plan (simulado, sin cobro). Queda registrado en el historial de cambios y en auditoría."""
    return subscriptions_service.change_plan(user.uid, body.plan_id, body.confirm_over_limit, user.uid, "user")
