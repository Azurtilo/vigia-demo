"""Nodos de detección (Edge), observaciones de postura y estado de la cámara (spec 019).

Solo metadatos: nunca imágenes, video ni coordenadas del cuerpo.
"""

from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.models.user import ApiModel

MonitorState = Literal["normal", "persona_no_visible", "sin_imagen", "poca_luz"]
# Estado agregado que ven todos los miembros (D-077); "sin_senal" lo calcula el servidor.
CameraStateValue = Literal["sin_senal", "sin_imagen", "poca_luz", "persona_no_visible", "normal"]


class NodeCreate(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Escribe un nombre de hasta 80 caracteres.")
        return value


class Node(ApiModel):
    id: str
    name: str
    active: bool
    last_seen_at: datetime | None = None
    connected: bool
    monitor_state: MonitorState | Literal["desconocido"] = "desconocido"
    monitor_since: datetime | None = None


class NodeCreated(Node):
    credential: str = Field(description="Token del nodo. Se muestra solo esta vez; el servidor guarda su SHA-256")


class NodeList(ApiModel):
    items: list[Node]


class CameraState(ApiModel):
    state: CameraStateValue | None = Field(
        description="Peor estado de los nodos activos; null sin nodos, sin cámara en el plan o sin estado informado"
    )


class Observation(ApiModel):
    id: str
    posture: str
    confidence: float
    observed_at: datetime
    received_at: datetime
    risk: str
    source: str
    source_type: Literal["fixed", "phone"]
    model_version: str
    rule_version: str


class ObservationPage(ApiModel):
    items: list[Observation]
    next_cursor: str | None = None
    enabled: bool
