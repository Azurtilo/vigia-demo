"""Registro de auditoría de acciones sensibles. No se guardan datos personales en `details`."""

from google.cloud import firestore

from app.core.firebase import get_db


def audit_ref() -> firestore.DocumentReference:
    return get_db().collection("auditLogs").document()


def audit_entry(actor: str, action: str, target: str, details: dict | None = None) -> dict:
    return {
        "actor": actor,
        "action": action,
        "target": target,
        "details": details or {},
        "createdAt": firestore.SERVER_TIMESTAMP,
    }


def write_audit(actor: str, action: str, target: str, details: dict | None = None) -> None:
    audit_ref().set(audit_entry(actor, action, target, details))
