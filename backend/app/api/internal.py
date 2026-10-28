"""Tick del cron externo (RF-019-08, D-088). No se publica en la documentación de la API.

cron-job.org llama cada minuto con la cabecera `X-Cron-Secret`. Sin secreto configurado el tick
está desactivado; con uno incorrecto responde 401 sin hacer nada.
"""

import hmac
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Header, status

from app.core.config import get_settings
from app.core.errors import AppError
from app.services import alerts, reminders

router = APIRouter(prefix="/internal", include_in_schema=False)


@router.post("/tick")
def tick(x_cron_secret: Annotated[str | None, Header()] = None) -> dict:
    secret = get_settings().cron_secret
    if not secret or not x_cron_secret or not hmac.compare_digest(secret.encode(), x_cron_secret.encode()):
        raise AppError(status.HTTP_401_UNAUTHORIZED, "cron_unauthorized", "No autorizado.")
    now = datetime.now(UTC)
    return {**alerts.run_cycle(now), "reminders_sent": reminders.run(now)}
