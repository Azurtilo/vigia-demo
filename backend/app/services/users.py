"""Reglas de negocio de usuarios. Única implementación, usada por la app y el portal."""

from fastapi import status
from google.api_core.exceptions import Aborted, AlreadyExists
from google.cloud import firestore

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.user import Role, UserProfile
from app.services import plans
from app.services.audit import audit_entry, audit_ref, write_audit

USERS = "users"


def _to_profile(snapshot: firestore.DocumentSnapshot) -> UserProfile:
    data = snapshot.to_dict() or {}
    return UserProfile(
        uid=snapshot.id,
        email=data.get("email"),
        display_name=data.get("displayName", ""),
        role=data.get("role", "client"),
        status=data.get("status", "active"),
        active_patient_count=data.get("activePatientCount", 0),
        created_at=data.get("createdAt"),
    )


def get_profile(uid: str) -> UserProfile | None:
    snapshot = get_db().collection(USERS).document(uid).get()
    return _to_profile(snapshot) if snapshot.exists else None


def register(uid: str, email: str | None, display_name: str) -> UserProfile:
    """Crea el perfil VIGIA con plan Gratis. El rol es siempre 'client': no lo decide quien se registra."""
    db = get_db()
    user_ref = db.collection(USERS).document(uid)
    # create() es atómico ("crear solo si no existe"): ante solicitudes simultáneas solo una
    # lo logra y las demás reciben AlreadyExists. No requiere leer antes ni tomar bloqueos.
    # El lote aplica perfil, suscripción y auditoría juntos, o ninguno.
    batch = db.batch()
    batch.create(
        user_ref,
        {
            "email": email,
            "displayName": display_name.strip(),
            "role": "client",
            "status": "active",
            "activePatientCount": 0,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        },
    )
    batch.create(plans.subscription_ref(uid), plans.new_subscription())
    batch.set(audit_ref(), audit_entry(actor=uid, action="user.registered", target=f"users/{uid}"))
    try:
        batch.commit()
    except AlreadyExists:
        raise AppError(status.HTTP_409_CONFLICT, "already_registered", "Tu cuenta ya está registrada.")
    except Aborted:
        # Con mucha contención Firestore puede abortar la escritura sin aplicarla.
        if user_ref.get().exists:
            raise AppError(status.HTTP_409_CONFLICT, "already_registered", "Tu cuenta ya está registrada.")
        raise AppError(
            status.HTTP_503_SERVICE_UNAVAILABLE, "service_busy", "Hay muchas solicitudes a la vez. Intenta nuevamente."
        )
    return _to_profile(user_ref.get())


def set_role(uid: str, role: Role, actor: str) -> UserProfile:
    """Cambia el rol de un usuario existente y lo deja auditado."""
    db = get_db()
    user_ref = db.collection(USERS).document(uid)

    @firestore.transactional
    def _apply(transaction: firestore.Transaction) -> str:
        snapshot = user_ref.get(transaction=transaction)
        if not snapshot.exists:
            raise AppError(status.HTTP_404_NOT_FOUND, "user_not_found", "El usuario no existe.")
        previous = snapshot.get("role")
        transaction.update(user_ref, {"role": role, "updatedAt": firestore.SERVER_TIMESTAMP})
        return previous

    previous = _apply(db.transaction())
    write_audit(actor, "user.role_changed", f"users/{uid}", {"from": previous, "to": role})
    return get_profile(uid)  # type: ignore[return-value]
