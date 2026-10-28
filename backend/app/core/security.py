"""Autenticación (¿quién eres?) y autorización base (¿tu cuenta puede operar?).

- `get_identity`: valida el token de Firebase. No exige perfil en VIGIA (sirve para registrarse).
- `get_registered_user`: además exige perfil registrado y cuenta activa.
- `get_current_user`: además exige la política de privacidad vigente aceptada (si está activada).
- `require_admin`: además exige rol de administrador.
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.firebase import init_firebase
from app.models.user import UserProfile
from app.services import users as users_service

_bearer = HTTPBearer(auto_error=False, description="ID token de Firebase Authentication")


@dataclass(frozen=True)
class Identity:
    uid: str
    email: str | None
    email_verified: bool
    auth_time: int | None = None  # cuándo inició sesión (segundos Unix); sirve para pedir reautenticación


def _unauthorized(code: str, message: str) -> AppError:
    return AppError(status.HTTP_401_UNAUTHORIZED, code, message)


def get_identity(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Identity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("auth_missing", "Debes iniciar sesión.")
    init_firebase()
    try:
        # check_revoked también rechaza tokens de cuentas deshabilitadas en Firebase Auth.
        decoded = auth.verify_id_token(credentials.credentials, check_revoked=True)
    except auth.ExpiredIdTokenError:
        raise _unauthorized("auth_expired", "Tu sesión expiró. Vuelve a iniciar sesión.")
    except auth.RevokedIdTokenError:
        raise _unauthorized("auth_revoked", "Tu sesión fue cerrada. Vuelve a iniciar sesión.")
    except auth.UserDisabledError:
        raise AppError(status.HTTP_403_FORBIDDEN, "account_disabled", "Tu cuenta está deshabilitada.")
    except (auth.InvalidIdTokenError, auth.UserNotFoundError, ValueError):
        # UserNotFoundError: token aún vigente de una cuenta que ya fue eliminada.
        raise _unauthorized("auth_invalid", "La sesión no es válida. Vuelve a iniciar sesión.")
    return Identity(
        uid=decoded["uid"],
        email=decoded.get("email"),
        email_verified=bool(decoded.get("email_verified", False)),
        auth_time=decoded.get("auth_time"),
    )


def get_registered_user(identity: Annotated[Identity, Depends(get_identity)]) -> UserProfile:
    """Perfil registrado y cuenta activa, sin exigir la política (sirve para consultarla y aceptarla)."""
    profile = users_service.get_profile(identity.uid)
    if profile is None:
        raise AppError(status.HTTP_403_FORBIDDEN, "profile_missing", "Debes completar tu registro en VIGIA.")
    if profile.status == "deleted":
        raise AppError(status.HTTP_403_FORBIDDEN, "account_deleted", "Esta cuenta fue eliminada.")
    if profile.status != "active":
        raise AppError(status.HTTP_403_FORBIDDEN, "account_suspended", "Tu cuenta está suspendida.")
    return profile


def get_current_user(user: Annotated[UserProfile, Depends(get_registered_user)]) -> UserProfile:
    """Además exige la política de privacidad vigente aceptada (spec 014), si está activada."""
    settings = get_settings()
    if settings.privacy_enforced and user.policy_accepted_version != settings.privacy_policy_version:
        raise AppError(
            status.HTTP_403_FORBIDDEN, "policy_not_accepted", "Acepta la política de privacidad para continuar."
        )
    return user


def require_admin(user: Annotated[UserProfile, Depends(get_current_user)]) -> UserProfile:
    if user.role != "admin":
        raise AppError(status.HTTP_403_FORBIDDEN, "forbidden", "No tienes permiso para esta acción.")
    return user
