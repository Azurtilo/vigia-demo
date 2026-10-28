"""Historial del paciente (lectura paginada)."""

from datetime import datetime
from typing import Any, Literal

from app.models.user import ApiModel

# medication: tomas · task: tareas · position: cambios de posición · change: altas/cambios de medicamentos y tareas
Category = Literal["medication", "task", "position", "change"]


class HistoryEntry(ApiModel):
    id: str
    type: str  # p. ej. "medication.given", "position.changed"
    category: Category
    occurred_at: datetime  # cuándo ocurrió
    recorded_at: datetime | None  # cuándo se registró (puede ser después)
    actor_uid: str
    actor_name: str
    data: dict[str, Any]


class HistoryPage(ApiModel):
    items: list[HistoryEntry]
    next_cursor: str | None  # enviar como `cursor` para la página siguiente; null = no hay más
    # Límite del plan del responsable: desde cuándo se muestra (null = sin límite).
    visible_since: datetime | None
    # True si existen registros más antiguos que el plan no muestra (se conservan, no se borran).
    hidden_older_entries: bool
