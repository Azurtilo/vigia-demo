"""Alertas de riesgo y de cámara, y registro de dispositivos para push (spec 019)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.models.user import ApiModel

AlertKind = Literal["fall", "immobility", "camera_blind", "node_offline"]
AlertStatus = Literal["open", "attended"]


class Alert(ApiModel):
    id: str
    patient_id: str
    patient_name: str | None = None
    kind: AlertKind
    monitor_state: str | None = Field(default=None, description="Solo en `camera_blind`: persona_no_visible o sin_imagen")
    occurred_at: datetime
    status: AlertStatus
    attended_by: str | None = None
    attended_at: datetime | None = None


class AlertPage(ApiModel):
    items: list[Alert]
    next_cursor: str | None = None


class _Strict(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class DeviceRegistration(_Strict):
    installation_id: UUID = Field(description="Identificador aleatorio de la instalación; uno nuevo por cuenta")
    enabled: bool
    token: str | None = Field(default=None, min_length=20, max_length=4096, description="Token FCM")
    platform: Literal["android", "ios"] | None = None
    local_posture_reminders: bool = False

    @model_validator(mode="after")
    def _token_when_enabled(self) -> "DeviceRegistration":
        if self.enabled and (self.token is None or self.platform is None):
            raise ValueError("Para activar los avisos se necesitan el token y la plataforma.")
        return self


class ReminderMode(_Strict):
    installation_id: UUID
    local_posture_reminders: bool
