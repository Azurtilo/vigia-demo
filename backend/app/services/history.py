"""Lectura del historial: del más reciente al más antiguo, paginado y limitado por el plan del dueño.

El límite de días del plan solo OCULTA lo antiguo; nunca se borra nada.
Costo por página: 1 consulta (limit+1 documentos) + 1 lectura por lote de nombres + 1 consulta de
1 documento para saber si hay registros ocultos.
"""

import base64
import binascii
import re
from datetime import UTC, datetime, timedelta

from fastapi import status
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.history import Category, HistoryEntry, HistoryPage
from app.services import patients as patients_service
from app.services.activity import activity_collection
from app.services.care_common import owner_features

_DOC_ID = re.compile(r"^[A-Za-z0-9]{1,64}$")


def _encode_cursor(doc_id: str) -> str:
    return base64.urlsafe_b64encode(doc_id.encode()).decode().rstrip("=")


def _decode_cursor(cursor: str) -> str:
    try:
        doc_id = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise _invalid_cursor() from None
    # Los IDs automáticos de Firestore son alfanuméricos; cualquier otra cosa (vacío, "/") se rechaza.
    if not _DOC_ID.match(doc_id):
        raise _invalid_cursor()
    return doc_id


def _invalid_cursor() -> AppError:
    return AppError(status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_cursor", "El cursor de página no es válido.")


def history(
    patient_id: str, uid: str, limit: int, cursor: str | None, category: Category | None
) -> HistoryPage:
    access = patients_service.get_access(patient_id, uid, "history.view")
    days = owner_features(access).get("historyDays")
    visible_since = datetime.now(UTC) - timedelta(days=days) if days else None

    collection = activity_collection(patient_id)
    query = collection
    if category:
        query = query.where(filter=FieldFilter("category", "==", category))
    if visible_since:
        query = query.where(filter=FieldFilter("occurredAt", ">=", visible_since))
    query = query.order_by("occurredAt", direction=firestore.Query.DESCENDING)

    if cursor:
        last = collection.document(_decode_cursor(cursor)).get()
        if not last.exists:
            raise _invalid_cursor()
        query = query.start_after(last)

    docs = list(query.limit(limit + 1).stream())
    page, has_more = docs[:limit], len(docs) > limit

    hidden = False
    if visible_since:
        older = collection.where(filter=FieldFilter("occurredAt", "<", visible_since))
        if category:
            older = older.where(filter=FieldFilter("category", "==", category))
        # Mismo orden que la consulta principal: reutiliza el índice (category, occurredAt DESC).
        older = older.order_by("occurredAt", direction=firestore.Query.DESCENDING)
        hidden = bool(list(older.limit(1).stream()))

    db = get_db()
    actor_ids = {d.get("actorUid") for d in page}
    names = {
        s.id: s.get("displayName")
        for s in (db.get_all([db.collection("users").document(a) for a in actor_ids]) if actor_ids else [])
        if s.exists
    }
    items = [
        HistoryEntry(
            id=d.id,
            type=d.get("type"),
            category=d.get("category"),
            occurred_at=d.get("occurredAt"),
            recorded_at=d.get("recordedAt"),
            actor_uid=d.get("actorUid"),
            actor_name=names.get(d.get("actorUid"), "(cuenta eliminada)"),
            data=d.get("data") or {},
        )
        for d in page
    ]
    return HistoryPage(
        items=items,
        next_cursor=_encode_cursor(page[-1].id) if has_more else None,
        visible_since=visible_since,
        hidden_older_entries=hidden,
    )
