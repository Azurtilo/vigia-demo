"""Autenticación, registro, roles y estado de cuenta contra los emuladores de Firebase."""

import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from firebase_admin import auth
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError, register_error_handlers
from app.core.firebase import get_db
from app.core.security import require_admin
from app.services import users as users_service
from tests.helpers import bearer, make_token, sign_up

pytestmark = pytest.mark.usefixtures("emulators")


def _register(client: TestClient, email: str, name: str = "Persona de prueba") -> tuple[str, str]:
    uid, token = sign_up(email)
    response = client.post("/v1/auth/register", json={"displayName": name}, headers=bearer(token))
    assert response.status_code == 201, response.text
    return uid, token


# ---------- Autenticación: ¿quién eres? ----------


def test_me_without_token_is_401(client):
    response = client.get("/v1/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_missing"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_me_with_garbage_token_is_401(client):
    response = client.get("/v1/me", headers=bearer("esto-no-es-un-token"))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_invalid"


def test_expired_token_is_401(client, monkeypatch):
    # En modo emulador el SDK NO verifica firma ni vencimiento (firebase_admin/_token_gen.py),
    # así que aquí se simula la respuesta del SDK ante un token vencido. Con Firebase real,
    # la verificación la hace google.oauth2.id_token.verify_token.
    def expired(*_args, **_kwargs):
        raise auth.ExpiredIdTokenError("Token expired", cause=None)

    monkeypatch.setattr(auth, "verify_id_token", expired)

    response = client.get("/v1/me", headers=bearer("token-vencido"))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_expired"


def test_token_from_another_project_is_401(client):
    uid, _ = sign_up("otro-proyecto@example.com")

    response = client.get("/v1/me", headers=bearer(make_token(uid, project="demo-otro")))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_invalid"


def test_token_of_deleted_account_is_401(client):
    uid, token = sign_up("borrada@example.com")
    auth.delete_user(uid)

    response = client.get("/v1/me", headers=bearer(token))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_invalid"


def test_disabled_firebase_account_is_403(client):
    uid, token = _register(client, "deshabilitada@example.com")
    auth.update_user(uid, disabled=True)

    response = client.get("/v1/me", headers=bearer(token))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "account_disabled"


# ---------- Registro ----------


def test_register_creates_client_profile_and_me_returns_it(client):
    uid, token = sign_up("ana@example.com")

    created = client.post("/v1/auth/register", json={"displayName": "  Ana  "}, headers=bearer(token))
    me = client.get("/v1/me", headers=bearer(token))

    assert created.status_code == 201
    assert me.status_code == 200
    body = me.json()
    assert body["uid"] == uid
    assert body["email"] == "ana@example.com"
    assert body["displayName"] == "Ana"
    assert body["role"] == "client"
    assert body["status"] == "active"
    assert body["activePatientCount"] == 0


def test_register_writes_audit_log(client):
    uid, _ = _register(client, "auditada@example.com")

    query = get_db().collection("auditLogs").where(filter=FieldFilter("target", "==", f"users/{uid}"))
    logs = [d.to_dict() for d in query.stream()]

    assert [log["action"] for log in logs] == ["user.registered"]
    assert logs[0]["actor"] == uid


def test_me_without_registration_is_403(client):
    _, token = sign_up("sin-registro@example.com")

    response = client.get("/v1/me", headers=bearer(token))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "profile_missing"


def test_register_cannot_self_assign_admin(client):
    uid, token = sign_up("tramposa@example.com")

    response = client.post(
        "/v1/auth/register", json={"displayName": "Tramposa", "role": "admin"}, headers=bearer(token)
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert not get_db().collection("users").document(uid).get().exists


def test_register_twice_is_409(client):
    _, token = _register(client, "doble@example.com")

    response = client.post("/v1/auth/register", json={"displayName": "Otra vez"}, headers=bearer(token))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "already_registered"


def test_simultaneous_registrations_never_create_two_profiles():
    uid, _ = sign_up("concurrente@example.com")

    def attempt(i: int) -> str:
        try:
            users_service.register(uid, "concurrente@example.com", f"Intento {i}")
            return "ok"
        except AppError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(attempt, range(5)))

    created = results.count("ok")
    audits = list(get_db().collection("auditLogs").where(filter=FieldFilter("action", "==", "user.registered")).stream())
    # Regla de negocio: como máximo un perfil, y cada intento termina en un resultado controlado.
    assert created <= 1, results
    assert set(results) <= {"ok", "already_registered", "service_busy"}, results
    assert get_db().collection("users").document(uid).get().exists == (created == 1)
    assert len(audits) == created


def test_validation_error_does_not_echo_values(client):
    _, token = sign_up("validacion@example.com")

    response = client.post("/v1/auth/register", json={"displayName": ""}, headers=bearer(token))

    error = response.json()["error"]
    assert response.status_code == 422
    assert error["details"] == [{"field": "body.displayName", "type": "string_too_short"}]
    assert "input" not in json.dumps(error)


# ---------- Estado de cuenta y roles ----------


def test_suspended_account_is_403(client):
    uid, token = _register(client, "suspendida@example.com")
    get_db().collection("users").document(uid).update({"status": "suspended"})

    response = client.get("/v1/me", headers=bearer(token))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "account_suspended"


@pytest.fixture
def admin_only_client() -> TestClient:
    """App mínima con una ruta protegida por require_admin, para probar la dependencia."""
    test_app = FastAPI()
    register_error_handlers(test_app)

    @test_app.get("/solo-admin")
    def solo_admin(_=Depends(require_admin)) -> dict:
        return {"ok": True}

    return TestClient(test_app)


def test_require_admin_rejects_client(client, admin_only_client):
    _, token = _register(client, "cliente@example.com")

    response = admin_only_client.get("/solo-admin", headers=bearer(token))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_set_role_promotes_to_admin_and_is_audited(client, admin_only_client):
    uid, token = _register(client, "futura-admin@example.com")

    users_service.set_role(uid, "admin", actor="script:create_admin")

    assert admin_only_client.get("/solo-admin", headers=bearer(token)).status_code == 200
    assert client.get("/v1/me", headers=bearer(token)).json()["role"] == "admin"
    query = get_db().collection("auditLogs").where(filter=FieldFilter("action", "==", "user.role_changed"))
    logs = [d.to_dict() for d in query.stream()]
    assert len(logs) == 1
    assert logs[0]["actor"] == "script:create_admin"
    assert logs[0]["details"] == {"from": "client", "to": "admin"}


def test_set_role_on_missing_user_is_404():
    with pytest.raises(AppError) as exc:
        users_service.set_role("no-existe", "admin", actor="script:create_admin")

    assert exc.value.code == "user_not_found"
