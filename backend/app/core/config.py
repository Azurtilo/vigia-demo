"""Configuración del backend leída desde variables de entorno (o archivo .env)."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


CRON_SECRET_MIN = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VIGIA_", env_file=".env", extra="ignore")

    app_name: str = "VIGIA API"
    # Sin declarar: "production" con Firebase real y "development" con emuladores (QA-2026-10-28-07).
    # Así, olvidar VIGIA_ENVIRONMENT en el servidor no desactiva protecciones de producción.
    environment: Literal["development", "test", "production"] | None = None
    # Se recibe como texto separado por comas para que sea fácil de definir en .env
    cors_origins: str = "http://localhost:5173"

    # Firebase. Un proyecto "demo-*" solo existe en los emuladores y nunca toca la nube.
    firebase_project_id: str = "demo-vigia"
    # host:puerto de los emuladores. Vacíos = usar los servicios reales de Firebase.
    auth_emulator_host: str = ""
    firestore_emulator_host: str = ""

    # Push con Firebase Cloud Messaging (VIGIA_PUSH_ENABLED). Apagado, las alertas se guardan
    # igual y quedan pendientes de envío; los emuladores no entregan push a teléfonos.
    push_enabled: bool = False

    # Privacidad (spec 014). Activada, la API exige aceptar la política vigente y el consentimiento
    # de cuidado del paciente para registrar datos. El consentimiento de detección se exige siempre.
    privacy_enforced: bool = True
    privacy_policy_version: str = "2026-10-25"

    # Secreto del cron externo para POST /internal/tick (VIGIA_CRON_SECRET). Vacío = tick desactivado.
    # En producción, si se define, debe tener al menos CRON_SECRET_MIN caracteres (QA-2026-10-28-08).
    cron_secret: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def uses_emulators(self) -> bool:
        return bool(self.auth_emulator_host or self.firestore_emulator_host)

    @model_validator(mode="after")
    def _check_environment(self) -> "Settings":
        if self.environment is None:
            self.environment = "development" if self.uses_emulators else "production"
        # Los emuladores aceptan tokens sin firma: jamás deben usarse en producción.
        if self.environment == "production" and self.uses_emulators:
            raise ValueError("En producción no se permiten emuladores de Firebase.")
        if self.uses_emulators and not self.firebase_project_id.startswith("demo-"):
            raise ValueError("Con emuladores, el proyecto debe llamarse 'demo-*' para no tocar datos reales.")
        if self.environment == "production" and self.cron_secret and len(self.cron_secret) < CRON_SECRET_MIN:
            raise ValueError(f"En producción, VIGIA_CRON_SECRET debe tener al menos {CRON_SECRET_MIN} caracteres.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
