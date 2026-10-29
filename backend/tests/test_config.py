import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_emulators():
    with pytest.raises(ValidationError, match="producción"):
        Settings(environment="production", auth_emulator_host="127.0.0.1:9099", _env_file=None)


def test_emulators_require_demo_project():
    with pytest.raises(ValidationError, match="demo-"):
        Settings(firebase_project_id="vigia-real", firestore_emulator_host="127.0.0.1:8080", _env_file=None)


# conftest.py define los emuladores en el entorno: aquí se anulan para simular Firebase real.
REAL_FIREBASE = {"firebase_project_id": "vigia-real", "auth_emulator_host": "", "firestore_emulator_host": "", "_env_file": None}


def test_undeclared_environment_is_production_without_emulators(monkeypatch):
    # QA-2026-10-28-07: olvidar VIGIA_ENVIRONMENT en el servidor no desactiva protecciones.
    monkeypatch.delenv("VIGIA_ENVIRONMENT", raising=False)
    real = Settings(**REAL_FIREBASE)
    local = Settings(firebase_project_id="demo-x", auth_emulator_host="127.0.0.1:9099", _env_file=None)

    assert (real.environment, local.environment) == ("production", "development")


@pytest.mark.parametrize("secret", ["corto", "x" * 31])
def test_production_rejects_a_short_cron_secret(secret):
    with pytest.raises(ValidationError, match="VIGIA_CRON_SECRET"):
        Settings(environment="production", cron_secret=secret, **REAL_FIREBASE)


def test_production_accepts_no_cron_secret_or_a_long_one():
    for secret in ("", "x" * 32):
        Settings(environment="production", cron_secret=secret, **REAL_FIREBASE)
    Settings(environment="development", firebase_project_id="demo-x", auth_emulator_host="h:1", cron_secret="corto", _env_file=None)


def test_production_hides_the_api_documentation(monkeypatch):
    # QA-2026-10-28-06: la app se arma al importar main.py, así que se vuelve a importar con producción.
    import importlib

    from fastapi.testclient import TestClient

    import app.main
    from app.core import config

    for name in ("VIGIA_AUTH_EMULATOR_HOST", "VIGIA_FIRESTORE_EMULATOR_HOST"):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("VIGIA_ENVIRONMENT", "production")
    monkeypatch.setenv("VIGIA_FIREBASE_PROJECT_ID", "vigia-real")
    config.get_settings.cache_clear()
    try:
        production = TestClient(importlib.reload(app.main).app)
        assert [production.get(p).status_code for p in ("/docs", "/redoc", "/openapi.json")] == [404, 404, 404]
        assert production.get("/health").json()["environment"] == "production"
    finally:
        monkeypatch.undo()
        config.get_settings.cache_clear()
        importlib.reload(app.main)
    assert TestClient(app.main.app).get("/openapi.json").status_code == 200


def test_production_without_emulators_is_valid():
    settings = Settings(
        environment="production",
        firebase_project_id="vigia-real",
        auth_emulator_host="",
        firestore_emulator_host="",
        _env_file=None,
    )
    assert not settings.uses_emulators
