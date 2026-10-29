"""Historial de actividad del paciente: un resumen por cada acción de cuidado.

Se escribe en el mismo lote/transacción que la acción, así el historial nunca queda desfasado.
Se guarda estructurado (tipo + datos); la app y el portal arman el texto a mostrar.
"""

from datetime import datetime

from google.cloud import firestore

from app.core.firebase import get_db
from app.models.history import Category

# Categorías para filtrar el historial (con índice category + occurredAt):
# - medication: tomas (dadas, retrasadas, omitidas, corregidas)
# - task: tareas realizadas, no realizadas o corregidas
# - position: cambios de posición
# - change: creación o modificación de medicamentos y tareas
_CHANGE_TYPES = {"medication.created", "medication.updated", "task.created", "task.updated"}


def category_of(type_: str) -> Category:
    if type_ in _CHANGE_TYPES:
        return "change"
    if type_ == "position.changed":
        return "position"
    return "medication" if type_.startswith("medication.") else "task"


def activity_collection(patient_id: str) -> firestore.CollectionReference:
    return get_db().collection("patients").document(patient_id).collection("activity")


def activity_ref(patient_id: str) -> firestore.DocumentReference:
    return activity_collection(patient_id).document()


def activity_entry(type_: str, actor_uid: str, occurred_at: datetime, data: dict) -> dict:
    return {
        "type": type_,
        "category": category_of(type_),
        "actorUid": actor_uid,
        "occurredAt": occurred_at,  # cuándo pasó (p. ej. hora real de la toma)
        "recordedAt": firestore.SERVER_TIMESTAMP,  # cuándo se registró
        "data": data,
    }
