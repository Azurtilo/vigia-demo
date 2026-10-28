"""Punto de entrada de la API de VIGIA."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import edge
from app.api.v1 import admin, care, medications, members, nodes, patients, subscriptions, users
from app.core.config import get_settings
from app.core.errors import UTF8JSONResponse, register_error_handlers

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="API REST de VIGIA. Herramienta de apoyo al cuidado; no es un dispositivo médico.",
    default_response_class=UTF8JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(users.router, prefix="/v1")
app.include_router(patients.router, prefix="/v1")
app.include_router(members.router, prefix="/v1")
app.include_router(medications.router, prefix="/v1")
app.include_router(care.router, prefix="/v1")
app.include_router(subscriptions.router, prefix="/v1")
app.include_router(admin.router, prefix="/v1")
app.include_router(nodes.router, prefix="/v1")
# El nodo Edge conserva la ruta de la API Django para no cambiar su código (D-086).
app.include_router(edge.router)


@app.get("/health", tags=["sistema"])
def health() -> dict[str, str]:
    """Indica que la API está en ejecución. No verifica servicios externos."""
    return {"status": "ok", "environment": settings.environment}
