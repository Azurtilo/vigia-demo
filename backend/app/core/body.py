"""Lectura del cuerpo de una solicitud con tope de tamaño (QA-2026-10-28-02).

`request.body()` carga todo en memoria antes de que se pueda revisar el tamaño; con un solo
proceso (D-084), un envío enorme podría dejar sin memoria al backend y cortar las alertas.
"""

from fastapi import Request


async def read_limited(request: Request, limit: int) -> bytes | None:
    """Devuelve el cuerpo si tiene hasta `limit` bytes; si es más grande, None, sin leer el resto."""
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            if int(declared) > limit:
                return None
        except ValueError:
            return None
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:  # sin Content-Length (chunked) o con uno falso
            return None
        chunks.append(chunk)
    return b"".join(chunks)
