"""Autorización de los nodos Edge en memoria (D-095, RF-019-11).

Un nodo renueva cada 10 s; leer cada vez nodo, paciente, plan y consentimiento agotaría la cuota
gratuita de Firestore. La decisión se guarda hasta AUTH_CACHE_SECONDS y se olvida al instante
cuando cambia algo que la afecta (revocación, plan, archivo, consentimiento). Supone un solo
proceso del backend (D-091). Este módulo no importa servicios para que cualquiera pueda llamar
a `forget` sin dependencias circulares.
"""

import threading
import time
from dataclasses import dataclass
from datetime import datetime

AUTH_CACHE_SECONDS = 60

# Reloj monotónico reemplazable en las pruebas.
clock = time.monotonic


@dataclass
class NodeAuth:
    node_id: str
    patient_id: str
    owner_uid: str
    node_name: str
    allowed: bool
    checked_at: float
    monitor_state: str | None = None
    last_seen: datetime | None = None  # en memoria; Firestore se actualiza como máximo cada 30 s
    seen_written_at: float = float("-inf")


_entries: dict[str, NodeAuth] = {}
_lock = threading.Lock()
_generation = 0


def lock() -> threading.Lock:
    return _lock


def generation() -> int:
    with _lock:
        return _generation


def fresh(credential_hash: str) -> NodeAuth | None:
    with _lock:
        entry = _entries.get(credential_hash)
        if entry and clock() - entry.checked_at < AUTH_CACHE_SECONDS:
            return entry
        return None


def previous(credential_hash: str) -> NodeAuth | None:
    with _lock:
        return _entries.get(credential_hash)


def store(credential_hash: str, entry: NodeAuth, loaded_at_generation: int) -> None:
    """Guarda la decisión salvo que algo se haya olvidado mientras se leía (sería obsoleta)."""
    with _lock:
        if loaded_at_generation == _generation:
            _entries[credential_hash] = entry


def drop(credential_hash: str) -> None:
    with _lock:
        _entries.pop(credential_hash, None)


def last_seen(node_id: str) -> datetime | None:
    with _lock:
        return next((e.last_seen for e in _entries.values() if e.node_id == node_id), None)


def forget(*, patient_id: str | None = None, owner_uid: str | None = None, everything: bool = False) -> None:
    global _generation
    with _lock:
        _generation += 1
        for key, entry in list(_entries.items()):
            if everything or entry.patient_id == patient_id or entry.owner_uid == owner_uid:
                del _entries[key]
