"""Esquemas de usuario. La API expone JSON en camelCase, igual que Firestore."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Role = Literal["client", "admin"]
AccountStatus = Literal["active", "suspended", "deleted"]


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RegisterRequest(ApiModel):
    # extra="forbid": si alguien envía "role" u otro campo, la solicitud se rechaza (422).
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid")

    display_name: str = Field(min_length=1, max_length=80)


class UserProfile(ApiModel):
    uid: str
    email: str | None
    display_name: str
    role: Role
    status: AccountStatus
    active_patient_count: int = 0
    created_at: datetime | None = None
    policy_accepted_version: str | None = None
