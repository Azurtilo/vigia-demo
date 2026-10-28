"""Configuración de pruebas.

Las pruebas de integración usan los emuladores de Firebase con un proyecto propio
(`demo-vigia-test`), así nunca tocan Firebase real ni los datos de desarrollo (`demo-vigia`).
Si los emuladores no están en ejecución, esas pruebas se marcan como OMITIDAS (no como aprobadas).
"""

import os
import socket

# Debe definirse antes de importar la app, que lee la configuración al cargarse.
os.environ["VIGIA_ENVIRONMENT"] = "test"
os.environ["VIGIA_FIREBASE_PROJECT_ID"] = "demo-vigia-test"
os.environ.setdefault("VIGIA_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
os.environ.setdefault("VIGIA_FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
# Como en Django (PRIVACY_ENFORCED=False en test_settings): las pruebas de privacidad la activan
# explícitamente (tests/test_privacy.py). El consentimiento de detección se exige siempre.
os.environ["VIGIA_PRIVACY_ENFORCED"] = "false"

import pytest  # noqa: E402
import requests  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from tests.helpers import AUTH_HOST, FIRESTORE_HOST, PROJECT  # noqa: E402


def _reachable(host_port: str) -> bool:
    host, port = host_port.rsplit(":", 1)
    try:
        with socket.create_connection((host, int(port)), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def emulators() -> None:
    """Exige emuladores activos y deja Auth y Firestore vacíos antes de cada prueba."""
    assert PROJECT.startswith("demo-"), "Las pruebas solo pueden correr contra proyectos demo-*"
    assert get_settings().firebase_project_id == PROJECT
    if not (_reachable(AUTH_HOST) and _reachable(FIRESTORE_HOST)):
        pytest.skip("Emuladores de Firebase no disponibles (ejecuta: firebase emulators:start)")
    requests.delete(f"http://{AUTH_HOST}/emulator/v1/projects/{PROJECT}/accounts", timeout=5).raise_for_status()
    requests.delete(
        f"http://{FIRESTORE_HOST}/emulator/v1/projects/{PROJECT}/databases/(default)/documents", timeout=5
    ).raise_for_status()


@pytest.fixture
def seeded_plans(emulators) -> None:
    """Emuladores limpios + planes por defecto cargados."""
    from app.services.plans import seed_plans

    seed_plans()
