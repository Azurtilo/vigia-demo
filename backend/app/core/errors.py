"""Formato único de errores de la API: {"error": {"code": ..., "message": ...}}."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class UTF8JSONResponse(JSONResponse):
    """JSON con la codificación declarada: algunos clientes (p. ej. PowerShell 5.1) asumen
    Latin-1 si falta y muestran mal las tildes ("mÃ©dico")."""

    media_type = "application/json; charset=utf-8"


class AppError(Exception):
    """Error de negocio con código estable (para la app) y mensaje en español (para la persona)."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def _body(code: str, message: str, details: list | None = None) -> dict:
    error: dict = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == status.HTTP_401_UNAUTHORIZED else None
        return UTF8JSONResponse(_body(exc.code, exc.message), status_code=exc.status_code, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Solo ubicación y tipo de error: no se devuelven los valores enviados (pueden ser datos personales).
        details = [{"field": ".".join(str(p) for p in e["loc"]), "type": e["type"]} for e in exc.errors()]
        return UTF8JSONResponse(
            _body("validation_error", "Los datos enviados no son válidos.", details),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        messages = {404: "Recurso no encontrado.", 405: "Método no permitido."}
        return UTF8JSONResponse(
            _body(f"http_{exc.status_code}", messages.get(exc.status_code, str(exc.detail))),
            status_code=exc.status_code,
        )
