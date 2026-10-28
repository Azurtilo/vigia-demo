"""Utilidades compartidas por las pruebas de integración con los emuladores.

El emulador de Auth emite los tokens de sus endpoints públicos (signUp, signIn) siempre para
el proyecto con que se inició (`demo-vigia`). Para mantener las pruebas aisladas en
`demo-vigia-test`, las cuentas se crean con Admin SDK en ese proyecto y los tokens se arman
con el mismo formato sin firma que emite el emulador. El backend los valida igual que a
los del emulador: proyecto (aud/iss), vigencia y existencia y estado de la cuenta.
"""

import base64
import json
import os
import time

from firebase_admin import auth

from app.core.firebase import init_firebase

PROJECT = os.environ["VIGIA_FIREBASE_PROJECT_ID"]
AUTH_HOST = os.environ["VIGIA_AUTH_EMULATOR_HOST"]
FIRESTORE_HOST = os.environ["VIGIA_FIRESTORE_EMULATOR_HOST"]


def make_token(
    uid: str,
    *,
    email: str | None = None,
    project: str = PROJECT,
    expires_in: int = 3600,
) -> str:
    """ID token sin firma (formato del emulador). Permite fabricar casos válidos e inválidos."""

    def b64(data: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    # Emitido "ahora": un token anterior a la creación de la cuenta se considera revocado.
    now = int(time.time())
    payload = {
        "iss": f"https://securetoken.google.com/{project}",
        "aud": project,
        "sub": uid,
        "user_id": uid,
        "auth_time": now,
        "iat": now,
        "exp": now + expires_in,
        "firebase": {"sign_in_provider": "password", "identities": {}},
    }
    if email:
        payload |= {"email": email, "email_verified": False}
    return f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64(payload)}."


def sign_up(email: str, password: str = "clave-de-prueba") -> tuple[str, str]:
    """Crea una cuenta en el emulador de Auth (proyecto de pruebas) y devuelve (uid, id_token)."""
    init_firebase()
    user = auth.create_user(email=email, password=password)
    return user.uid, make_token(user.uid, email=email)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(client, email: str, name: str = "Persona de prueba") -> tuple[str, dict[str, str]]:
    """Crea cuenta + perfil VIGIA y devuelve (uid, encabezados de autorización)."""
    uid, token = sign_up(email)
    response = client.post("/v1/auth/register", json={"displayName": name}, headers=bearer(token))
    assert response.status_code == 201, response.text
    return uid, bearer(token)


def add_member(patient_id: str, uid: str, relation: str = "caregiver", permissions: list[str] | None = None) -> None:
    """Da acceso directo a un paciente (el flujo real con invitaciones se prueba en test_members)."""
    from app.core.firebase import get_db
    from app.core.permissions import DEFAULT_PERMISSIONS

    get_db().collection("memberships").document(f"{patient_id}_{uid}").set(
        {
            "patientId": patient_id,
            "uid": uid,
            "relation": relation,
            "permissions": permissions if permissions is not None else list(DEFAULT_PERMISSIONS[relation]),
        }
    )


def set_plan(uid: str, plan_id: str) -> None:
    """Cambia el plan directamente en Firestore (el cambio por API llega en la Fase 5)."""
    from app.services.plans import subscription_ref

    subscription_ref(uid).update({"planId": plan_id})
