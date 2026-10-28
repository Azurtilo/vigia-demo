"""Endpoints de nodos de detección, cámara del teléfono y observaciones. La autorización ocurre en app.services."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.core.errors import UTF8JSONResponse
from app.core.security import get_current_user
from app.models.nodes import CameraState, NodeCreate, NodeCreated, NodeList, ObservationPage
from app.models.user import UserProfile
from app.services import nodes as nodes_service

router = APIRouter(tags=["detección"])

CurrentUser = Annotated[UserProfile, Depends(get_current_user)]

_errors = {
    401: {"description": "Sin sesión o sesión inválida"},
    403: {"description": "Sin permiso, solo el responsable, cámara fuera del plan o sin consentimiento de detección"},
    404: {"description": "Paciente o nodo no encontrado"},
    409: {"description": "Paciente archivado o ya hay un nodo activo"},
}


@router.get("/patients/{patient_id}/nodes", response_model=NodeList, responses=_errors)
def list_nodes(patient_id: str, user: CurrentUser) -> NodeList:
    """Nodos del paciente con su conexión y estado de monitoreo. Solo el responsable."""
    return nodes_service.list_nodes(patient_id, user.uid)


@router.post(
    "/patients/{patient_id}/nodes", response_model=NodeCreated, status_code=status.HTTP_201_CREATED, responses=_errors
)
def link_node(patient_id: str, body: NodeCreate, user: CurrentUser) -> NodeCreated:
    """Vincula un nodo y entrega su token una sola vez. Un nodo activo por paciente."""
    return nodes_service.link_node(patient_id, user.uid, body.name)


@router.post("/nodes/{node_id}/revoke", responses=_errors)
def revoke_node(node_id: str, user: CurrentUser) -> dict:
    """Revoca el nodo: deja de ser aceptado de inmediato. Solo el responsable."""
    return nodes_service.revoke_node(node_id, user.uid)


@router.get("/patients/{patient_id}/camera", response_model=CameraState, responses=_errors)
def camera_state(patient_id: str, user: CurrentUser) -> CameraState:
    """Estado agregado de la cámara, de solo lectura para todos los miembros (D-077)."""
    return nodes_service.camera_state(patient_id, user.uid)


@router.get("/patients/{patient_id}/observations", response_model=ObservationPage, responses=_errors)
def list_observations(patient_id: str, user: CurrentUser, cursor: str | None = None) -> ObservationPage:
    """Observaciones de postura (nodo y teléfono), de a 30. Requiere `alerts.handle`."""
    return nodes_service.list_observations(patient_id, user.uid, cursor)


@router.get("/patients/{patient_id}/phone-observations", responses=_errors)
def phone_status(patient_id: str, user: CurrentUser) -> dict:
    """Indica si el análisis con la cámara del teléfono está disponible. Requiere `care.record`."""
    return nodes_service.phone_status(patient_id, user.uid)


@router.post("/patients/{patient_id}/phone-observations", responses=_errors)
async def phone_observation(patient_id: str, request: Request, user: CurrentUser) -> JSONResponse:
    """Análisis puntual del teléfono: 7 claves de metadatos, sin imagen ni coordenadas."""
    body = await request.body()
    code, result = await run_in_threadpool(nodes_service.phone_observation, patient_id, user.uid, body)
    return UTF8JSONResponse(result, status_code=code)
