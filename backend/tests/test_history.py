"""Historial: orden, paginación, filtros, permisos y límite visible según el plan del dueño."""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.firebase import get_db
from tests.helpers import add_member, register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


@pytest.fixture
def ctx(client):
    owner_uid, owner = register(client, "duena@example.com", "Dueña")
    carer_uid, carer = register(client, "cuidadora@example.com", "Cuidadora")
    pid = client.post("/v1/patients", json={"displayName": "Abuela"}, headers=owner).json()["id"]
    add_member(pid, carer_uid, "caregiver")
    med_id = client.post(
        f"/v1/patients/{pid}/medications",
        json={"name": "Ibuprofeno", "dose": "1 comprimido", "scheduleType": "as_needed", "startDate": "2025-01-01"},
        headers=owner,
    ).json()["id"]
    return {"owner": owner, "owner_uid": owner_uid, "carer": carer, "carer_uid": carer_uid, "pid": pid, "med": med_id}


def _give(client, ctx, when: datetime, headers=None):
    response = client.post(
        f"/v1/patients/{ctx['pid']}/medications/{ctx['med']}/doses",
        json={"status": "given", "actualAt": _iso(when)},
        headers=headers or ctx["carer"],
    )
    assert response.status_code == 201, response.text


def _history(client, ctx, headers=None, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return client.get(f"/v1/patients/{ctx['pid']}/history?{query}", headers=headers or ctx["owner"])


def test_history_is_newest_first_with_actor_names(client, ctx):
    now = datetime.now(UTC)
    _give(client, ctx, now - timedelta(hours=5))
    _give(client, ctx, now - timedelta(hours=1), headers=ctx["owner"])

    page = _history(client, ctx).json()

    assert [(i["type"], i["actorName"]) for i in page["items"]] == [
        ("medication.created", "Dueña"),  # ahora
        ("medication.given", "Dueña"),  # hace 1 h
        ("medication.given", "Cuidadora"),  # hace 5 h
    ]
    assert page["nextCursor"] is None
    assert page["items"][1]["data"]["name"] == "Ibuprofeno"


def test_late_record_is_placed_when_it_happened(client, ctx):
    now = datetime.now(UTC)
    _give(client, ctx, now - timedelta(hours=1))
    _give(client, ctx, now - timedelta(hours=3))  # registrada después, pero ocurrió antes

    times = [i["occurredAt"] for i in _history(client, ctx, category="medication").json()["items"]]

    assert times == sorted(times, reverse=True)


def test_pagination_returns_every_entry_once(client, ctx):
    now = datetime.now(UTC)
    for h in range(1, 6):
        _give(client, ctx, now - timedelta(hours=h))

    seen, cursor, pages = [], None, 0
    while True:
        params = {"limit": 2, **({"cursor": cursor} if cursor else {})}
        page = _history(client, ctx, **params).json()
        seen += [i["id"] for i in page["items"]]
        pages += 1
        cursor = page["nextCursor"]
        if not cursor:
            break

    assert pages == 3 and len(seen) == 6 and len(set(seen)) == 6  # 5 tomas + alta del medicamento


def test_category_filter(client, ctx):
    _give(client, ctx, datetime.now(UTC) - timedelta(hours=1))

    meds = _history(client, ctx, category="medication").json()["items"]
    changes = _history(client, ctx, category="change").json()["items"]

    assert [i["type"] for i in meds] == ["medication.given"]
    assert [i["type"] for i in changes] == ["medication.created"]
    assert _history(client, ctx, category="otra").status_code == 422


def test_free_plan_hides_but_keeps_entries_older_than_30_days(client, ctx):
    now = datetime.now(UTC)
    _give(client, ctx, now - timedelta(days=40))
    _give(client, ctx, now - timedelta(days=2))

    free = _history(client, ctx, category="medication").json()
    set_plan(ctx["owner_uid"], "plus")
    plus = _history(client, ctx, category="medication").json()

    assert len(free["items"]) == 1 and free["hiddenOlderEntries"] is True
    assert free["visibleSince"] is not None
    assert len(plus["items"]) == 2 and plus["hiddenOlderEntries"] is False
    # Nada se borró: las 2 tomas siguen guardadas.
    assert len(get_db().collection(f"patients/{ctx['pid']}/activity").get()) == 3


def test_premium_shows_everything(client, ctx):
    set_plan(ctx["owner_uid"], "premium")
    _give(client, ctx, datetime.now(UTC) - timedelta(days=400))

    page = _history(client, ctx, category="medication").json()

    assert len(page["items"]) == 1 and page["visibleSince"] is None and page["hiddenOlderEntries"] is False


def test_history_permissions(client, ctx):
    viewer_uid, viewer = register(client, "sin-historial@example.com")
    add_member(ctx["pid"], viewer_uid, "caregiver", ["patient.view"])
    _, stranger = register(client, "extrana@example.com")

    assert _history(client, ctx, headers=ctx["carer"]).status_code == 200  # cuidadora tiene history.view
    assert _history(client, ctx, headers=viewer).json()["error"]["code"] == "forbidden"
    assert _history(client, ctx, headers=stranger).status_code == 404


def test_history_includes_reasons(client, ctx):
    med_id = client.post(
        f"/v1/patients/{ctx['pid']}/medications",
        json={"name": "Paracetamol", "dose": "1 comprimido", "scheduleType": "fixed",
              "schedule": {"times": ["08:00"]}, "startDate": "2026-01-01"},
        headers=ctx["owner"],
    ).json()["id"]
    set_plan(ctx["owner_uid"], "premium")  # la toma es de enero: visible solo sin límite
    client.post(
        f"/v1/patients/{ctx['pid']}/medications/{med_id}/doses",
        json={"status": "omitted", "scheduledAt": "2026-01-15T11:00:00Z", "reason": "Se negó a tomarlo"},
        headers=ctx["carer"],
    )

    entry = _history(client, ctx, category="medication").json()["items"][0]

    assert entry["type"] == "medication.omitted"
    assert entry["data"]["reason"] == "Se negó a tomarlo"


@pytest.mark.parametrize("params", [{"cursor": "no-existe"}, {"cursor": "%%%"}, {"limit": 0}, {"limit": 101}])
def test_invalid_page_parameters(client, ctx, params):
    assert _history(client, ctx, **params).status_code == 422
