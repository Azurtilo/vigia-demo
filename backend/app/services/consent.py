"""Consentimiento del paciente por finalidad (spec 014, RF-019-07).

Falla cerrado: sin un registro activo no hay permiso. El registro y la revocación desde la
API llegan en T-019-06; aquí solo se consulta.
"""

from typing import Literal

from google.cloud import firestore

from app.core.firebase import get_db

Scope = Literal["cuidado", "deteccion"]


def consent_ref(patient_id: str, scope: Scope) -> firestore.DocumentReference:
    return get_db().collection("patients").document(patient_id).collection("consents").document(scope)


def is_active(patient_id: str, scope: Scope, transaction: firestore.Transaction | None = None) -> bool:
    snapshot = consent_ref(patient_id, scope).get(transaction=transaction)
    return snapshot.exists and snapshot.get("active") is True
