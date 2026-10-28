"""Esquemas de administración de planes y suscripciones."""

from datetime import datetime
from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.models.subscription import PlanId
from app.models.user import ApiModel

PriceClp = Annotated[int, Field(ge=0, le=1_000_000)]


class _Strict(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class PlanFeaturesUpdate(_Strict):
    """Solo cambia lo enviado. `historyDays: null` = historial sin límite."""

    extended_care_tracking: bool | None = None
    position_changes: bool | None = None
    history_days: Annotated[int, Field(ge=1, le=3650)] | None = None
    pdf_report: bool | None = None
    cameras: bool | None = None
    advanced_alerts: bool | None = None


class PlanUpdate(_Strict):
    """Solo cambia lo enviado. `maxPatients: null` = sin límite. `priceIsTest` no es editable en el MVP."""

    name: str | None = Field(default=None, min_length=1, max_length=40)
    price_clp: PriceClp | None = None
    max_patients: Annotated[int, Field(ge=1, le=1000)] | None = None
    available: bool | None = None
    features: PlanFeaturesUpdate | None = None


class AdminSubscriptionRow(ApiModel):
    uid: str
    email: str | None
    display_name: str | None
    plan_id: PlanId
    status: str
    started_at: datetime | None
    active_patients: int


class AdminSubscriptionPage(ApiModel):
    items: list[AdminSubscriptionRow]
    next_cursor: str | None
