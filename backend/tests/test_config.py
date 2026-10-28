import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_emulators():
    with pytest.raises(ValidationError, match="producción"):
        Settings(environment="production", auth_emulator_host="127.0.0.1:9099", _env_file=None)


def test_emulators_require_demo_project():
    with pytest.raises(ValidationError, match="demo-"):
        Settings(firebase_project_id="vigia-real", firestore_emulator_host="127.0.0.1:8080", _env_file=None)


def test_production_without_emulators_is_valid():
    settings = Settings(
        environment="production",
        firebase_project_id="vigia-real",
        auth_emulator_host="",
        firestore_emulator_host="",
        _env_file=None,
    )
    assert not settings.uses_emulators
