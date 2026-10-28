"""Planes y suscripciones simuladas (el MVP no cobra: `simulated` y `priceIsTest` siempre verdaderos)."""

from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.models.patient import PlanUsage
from app.models.user import ApiModel

PlanId = Literal["free", "plus", "premium"]


class PlanFeatures(ApiModel):
    extended_care_tracking: bool
    position_changes: bool
    history_days: int | None  # None = sin límite
    pdf_report: bool
    cameras: bool
    advanced_alerts: bool


class Plan(ApiModel):
    id: PlanId
    name: str
    order: int
    max_patients: int | None  # None = sin límite
    price_clp: int
    price_is_test: bool  # siempre True en el MVP: no son precios comerciales
    available: bool  # False: quien ya lo tiene lo conserva, pero no se puede elegir
    features: PlanFeatures


class SubscriptionChange(ApiModel):
    id: str
    from_plan: PlanId | None
    to_plan: PlanId
    changed_by: str
    actor_role: Literal["user", "admin"]
    price_clp: int  # precio de prueba vigente al momento del cambio
    price_is_test: bool
    over_limit_confirmed: bool
    at: datetime | None


class Subscription(ApiModel):
    plan_id: PlanId
    plan_name: str
    status: Literal["active"]
    simulated: bool
    started_at: datetime | None  # desde cuándo tiene el plan actual
    usage: PlanUsage
    recent_changes: list[SubscriptionChange]


class PlanChangePreview(ApiModel):
    current_plan_id: PlanId
    target: Plan
    active_patients: int
    over_limit: bool  # quedaría con más pacientes activos que el límite del nuevo plan
    lost_features: list[str]  # nombres legibles de lo que dejaría de tener
    requires_confirmation: bool
    message: str


class PlanChangeRequest(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    plan_id: PlanId
    # Obligatorio al bajar a un plan cuyo límite ya se supera (ver preview).
    confirm_over_limit: bool = Field(default=False)
