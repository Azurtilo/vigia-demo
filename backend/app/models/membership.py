"""Esquemas de miembros e invitaciones."""

from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, EmailStr, Field, field_validator
from pydantic.alias_generators import to_camel

from app.core.permissions import Permission, Relation
from app.models.user import ApiModel

InvitedRelation = Literal["family", "caregiver"]  # "owner" nunca se puede invitar
InvitationStatus = Literal["pending", "accepted", "revoked", "expired"]


def _check_permissions(value: list[Permission] | None) -> list[Permission] | None:
    if value is None:
        return value
    if "patient.view" not in value:
        raise ValueError("Todo miembro necesita el permiso patient.view para ver al paciente.")
    return sorted(set(value))


class _Strict(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class InvitationCreate(_Strict):
    email: EmailStr
    relation: InvitedRelation
    # Opcional: si no se envía, se usan los permisos por defecto de la relación.
    permissions: list[Permission] | None = Field(default=None, min_length=1)

    _valid_permissions = field_validator("permissions")(_check_permissions)


class Invitation(ApiModel):
    id: str
    patient_id: str
    email: str
    relation: InvitedRelation
    permissions: list[Permission]
    status: InvitationStatus
    created_at: datetime | None = None
    expires_at: datetime


class InvitationCreated(ApiModel):
    invitation: Invitation
    # Se muestra UNA sola vez: en la base de datos solo queda su huella (hash).
    code: str


class AcceptInvitation(_Strict):
    code: str = Field(min_length=10, max_length=40)


class Member(ApiModel):
    uid: str
    display_name: str
    relation: Relation
    permissions: list[Permission]


class MemberUpdate(_Strict):
    permissions: list[Permission] = Field(min_length=1)

    _valid_permissions = field_validator("permissions")(_check_permissions)
