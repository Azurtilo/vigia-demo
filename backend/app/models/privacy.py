"""Política de privacidad y consentimiento del paciente por finalidad (spec 014, RF-019-07)."""

from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.models.user import ApiModel

Scope = Literal["cuidado", "deteccion"]
Basis = Literal["titular", "representante"]


class PolicyStatus(ApiModel):
    policy_version: str
    accepted: bool
    accepted_version: str | None = None
    enforced: bool


class ConsentCreate(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    scope: Scope
    basis: Basis = Field(description="Quién consiente: el propio paciente o un representante")
    representative_name: str | None = Field(default=None, max_length=120)
    representative_relation: str | None = Field(default=None, max_length=60)

    @model_validator(mode="after")
    def _representative(self) -> "ConsentCreate":
        name = (self.representative_name or "").strip()
        relation = (self.representative_relation or "").strip()
        if self.basis == "representante" and not (name and relation):
            raise ValueError("Indica nombre y relación del representante.")
        if self.basis == "titular" and (name or relation):
            raise ValueError("Los datos del representante solo se usan cuando consiente un representante.")
        self.representative_name, self.representative_relation = name or None, relation or None
        return self


class PatientConsent(ApiModel):
    scope: Scope
    active: bool
    basis: Basis | None = None
    representative_name: str | None = None
    representative_relation: str | None = None
    policy_version: str | None = None
    recorded_by: str | None = None
    recorded_at: datetime | None = None
    revoked_at: datetime | None = None


class PatientConsents(ApiModel):
    items: list[PatientConsent]
