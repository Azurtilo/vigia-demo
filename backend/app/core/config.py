"""Configuración del backend leída desde variables de entorno (o archivo .env)."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VIGIA_", env_file=".env", extra="ignore")

    app_name: str = "VIGIA API"
    environment: Literal["development", "test", "production"] = "development"
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

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def uses_emulators(self) -> bool:
        return bool(self.auth_emulator_host or self.firestore_emulator_host)

    @model_validator(mode="after")
    def _check_environment(self) -> "Settings":
        # Los emuladores aceptan tokens sin firma: jamás deben usarse en producción.
        if self.environment == "production" and self.uses_emulators:
            raise ValueError("En producción no se permiten emuladores de Firebase.")
        if self.uses_emulators and not self.firebase_project_id.startswith("demo-"):
            raise ValueError("Con emuladores, el proyecto debe llamarse 'demo-*' para no tocar datos reales.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
