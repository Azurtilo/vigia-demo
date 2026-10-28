"""Contrato del nodo Edge en la misma ruta de la API Django (`/api/v1/edge`, D-086).

El nodo se autentica con su token (`Authorization: Bearer`), no con Firebase Auth. Las respuestas
no se guardan en cachés intermedias.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from app.core.errors import AppError, UTF8JSONResponse
from app.services import nodes as nodes_service

router = APIRouter(prefix="/api/v1/edge", tags=["nodo Edge"])

_NO_STORE = {"Cache-Control": "no-store, private"}


async def _respond(fn, *args) -> JSONResponse:
    followup = None
    try:
        code, body, followup = await run_in_threadpool(fn, *args)
    except AppError as exc:
        code, body = exc.status_code, {"error": {"code": exc.code, "message": exc.message}}
    # El push de una caída sale después de responder: el nodo nunca espera a FCM (D-051).
    background = BackgroundTask(followup) if followup else None
    return UTF8JSONResponse(body, status_code=code, headers=_NO_STORE, background=background)


def _status(header: str, query: list[tuple[str, str]]) -> tuple[int, dict, None]:
    return 200, nodes_service.edge_status(header, query), None


@router.get("/status")
async def edge_status(request: Request) -> JSONResponse:
    """Renovación del permiso de captura (`lease_seconds`) y estado de monitoreo opcional."""
    return await _respond(_status, request.headers.get("Authorization", ""), request.query_params.multi_items())


@router.post("/observations")
async def edge_observation(request: Request) -> JSONResponse:
    """Una observación de postura: exactamente las 7 claves del contrato, hasta 4 KB."""
    body = await request.body()
    return await _respond(
        nodes_service.edge_observation,
        request.headers.get("Authorization", ""),
        request.headers.get("Content-Type", ""),
        body,
    )
