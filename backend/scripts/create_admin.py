"""Otorga el rol de administrador a una cuenta VIGIA ya registrada.

Es la ÚNICA vía para crear administradores: la API pública nunca lo permite.
Requiere acceso de servidor (emulador o credenciales de Google Cloud), no un token de usuario.

Uso (desde backend/, con el entorno virtual activo):
    python -m scripts.create_admin correo@ejemplo.com
"""

import argparse
import sys

from firebase_admin import auth

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.firebase import init_firebase
from app.services import users as users_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Otorga el rol de administrador a una cuenta registrada.")
    parser.add_argument("email", help="Correo de la cuenta (ya registrada en VIGIA)")
    parser.add_argument("--yes", action="store_true", help="No pedir confirmación")
    args = parser.parse_args()

    settings = get_settings()
    target = "EMULADOR LOCAL" if settings.uses_emulators else "FIREBASE REAL"
    print(f"Proyecto: {settings.firebase_project_id} ({target})")

    init_firebase()
    try:
        user = auth.get_user_by_email(args.email)
    except auth.UserNotFoundError:
        print("No existe una cuenta de Firebase Authentication con ese correo.", file=sys.stderr)
        return 1

    profile = users_service.get_profile(user.uid)
    if profile is None:
        print("La cuenta existe en Authentication, pero no completó su registro en VIGIA.", file=sys.stderr)
        return 1
    if profile.role == "admin":
        print("La cuenta ya es administradora. No se hizo ningún cambio.")
        return 0

    if not args.yes:
        answer = input(f"¿Otorgar rol de administrador a {args.email}? Escribe 'si' para confirmar: ")
        if answer.strip().lower() not in {"si", "sí"}:
            print("Cancelado.")
            return 1

    try:
        users_service.set_role(user.uid, "admin", actor="script:create_admin")
    except AppError as exc:
        print(exc.message, file=sys.stderr)
        return 1
    print("Listo: la cuenta ahora es administradora. El cambio quedó en auditLogs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
