"""Administración de planes y suscripciones: acceso solo admin, reglas del plan Gratis y auditoría."""

import pytest
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.firebase import get_db
from app.services import users as users_service
from tests.helpers import register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")


@pytest.fixture
def admin(client):
    uid, headers = register(client, "admin@example.com", "Admin")
    users_service.set_role(uid, "admin", actor="script:create_admin")
    return {"uid": uid, "h": headers}


@pytest.fixture
def client_user(client):
    uid, headers = register(client, "clienta@example.com", "Clienta")
    return {"uid": uid, "h": headers}


def _patch_plan(client, headers, plan_id, body):
    return client.patch(f"/v1/admin/plans/{plan_id}", json=body, headers=headers)


def _code(response):
    return response.json()["error"]["code"]


# ---------- Solo administradores ----------


def test_non_admin_cannot_use_admin_endpoints(client, client_user):
    h = client_user["h"]
    calls = [
        client.get("/v1/admin/plans", headers=h),
        _patch_plan(client, h, "plus", {"priceClp": 1}),
        client.get("/v1/admin/subscriptions", headers=h),
        client.post(f"/v1/admin/users/{client_user['uid']}/subscription", json={"planId": "premium"}, headers=h),
    ]

    assert [c.status_code for c in calls] == [403] * 4
    assert {_code(c) for c in calls} == {"forbidden"}
    assert client.get("/v1/me/subscription", headers=h).json()["planId"] == "free"  # no se cambió nada
    assert client.get("/v1/admin/plans").status_code == 401


def test_suspended_admin_loses_access(client, admin):
    get_db().collection("users").document(admin["uid"]).update({"status": "suspended"})

    assert _code(client.get("/v1/admin/plans", headers=admin["h"])) == "account_suspended"


# ---------- Editar planes ----------


def test_admin_edits_price_and_it_is_audited(client, admin, client_user):
    response = _patch_plan(client, admin["h"], "plus", {"priceClp": 5990})

    plans = {p["id"]: p for p in client.get("/v1/plans", headers=client_user["h"]).json()}
    log = next(d.to_dict() for d in get_db().collection("auditLogs").where(filter=FieldFilter("action", "==", "plan.updated")).stream())
    assert response.status_code == 200 and response.json()["priceIsTest"] is True
    assert plans["plus"]["priceClp"] == 5990
    assert log["actor"] == admin["uid"]
    assert log["details"] == {"before": {"priceClp": 4990}, "after": {"priceClp": 5990}}


def test_past_changes_keep_the_price_they_had(client, admin, client_user):
    client.post("/v1/me/subscription/change", json={"planId": "plus"}, headers=client_user["h"])

    _patch_plan(client, admin["h"], "plus", {"priceClp": 7990})

    change = client.get("/v1/me/subscription", headers=client_user["h"]).json()["recentChanges"][0]
    assert change["priceClp"] == 4990


def test_partial_feature_update(client, admin):
    response = _patch_plan(client, admin["h"], "plus", {"features": {"pdfReport": False, "historyDays": 180}})

    features = response.json()["features"]
    assert features["pdfReport"] is False and features["historyDays"] == 180
    assert features["positionChanges"] is True  # no enviado = sin cambios


def test_lowering_patient_limit_keeps_existing_patients(client, admin, client_user):
    set_plan(client_user["uid"], "plus")
    for i in range(3):
        client.post("/v1/patients", json={"displayName": f"P{i}"}, headers=client_user["h"])

    _patch_plan(client, admin["h"], "plus", {"maxPatients": 2})

    assert len(client.get("/v1/patients", headers=client_user["h"]).json()) == 3
    assert _code(client.post("/v1/patients", json={"displayName": "Nuevo"}, headers=client_user["h"])) == "plan_limit_reached"


def test_unlimited_patients_with_null(client, admin):
    assert _patch_plan(client, admin["h"], "plus", {"maxPatients": None}).json()["maxPatients"] is None


@pytest.mark.parametrize(
    ("body", "code"),
    [({"priceClp": 990}, "free_plan_price_fixed"), ({"available": False}, "free_plan_always_available")],
)
def test_free_plan_rules(client, admin, body, code):
    assert _code(_patch_plan(client, admin["h"], "free", body)) == code


@pytest.mark.parametrize(
    "body",
    [
        {"priceClp": -1},
        {"priceClp": 2_000_000},
        {"maxPatients": 0},
        {"priceIsTest": False},  # no editable en el MVP
        {"name": ""},
        {"name": None},
        {"features": {"cameras": None}},
        {"features": {"teletransporte": True}},
    ],
)
def test_invalid_plan_updates(client, admin, body):
    assert _patch_plan(client, admin["h"], "plus", body).status_code == 422


def test_unknown_plan(client, admin):
    assert _patch_plan(client, admin["h"], "gold", {"priceClp": 1}).status_code == 422


def test_admin_sees_unavailable_plans(client, admin):
    _patch_plan(client, admin["h"], "premium", {"available": False})

    admin_ids = [p["id"] for p in client.get("/v1/admin/plans", headers=admin["h"]).json()]
    public_ids = [p["id"] for p in client.get("/v1/plans", headers=admin["h"]).json()]

    assert admin_ids == ["free", "plus", "premium"] and public_ids == ["free", "plus"]


# ---------- Suscripciones de usuarios ----------


def test_admin_changes_a_user_plan_and_it_is_attributed_to_admin(client, admin, client_user):
    response = client.post(
        f"/v1/admin/users/{client_user['uid']}/subscription", json={"planId": "premium"}, headers=admin["h"]
    )

    change = response.json()["recentChanges"][0]
    assert response.json()["planId"] == "premium"
    assert change["changedBy"] == admin["uid"] and change["actorRole"] == "admin"


def test_admin_can_assign_unavailable_plan_and_must_confirm_over_limit(client, admin, client_user):
    set_plan(client_user["uid"], "plus")
    for i in range(2):
        client.post("/v1/patients", json={"displayName": f"P{i}"}, headers=client_user["h"])
    _patch_plan(client, admin["h"], "premium", {"available": False})
    url = f"/v1/admin/users/{client_user['uid']}/subscription"

    premium = client.post(url, json={"planId": "premium"}, headers=admin["h"])
    free = client.post(url, json={"planId": "free"}, headers=admin["h"])
    free_ok = client.post(url, json={"planId": "free", "confirmOverLimit": True}, headers=admin["h"])

    assert premium.status_code == 200
    assert _code(free) == "downgrade_over_limit"
    assert free_ok.json()["planId"] == "free"


def test_admin_change_for_unknown_user(client, admin):
    response = client.post("/v1/admin/users/noExiste123/subscription", json={"planId": "plus"}, headers=admin["h"])

    assert _code(response) == "user_not_found"


def test_subscriptions_list_filters_and_paginates(client, admin):
    for i in range(4):
        uid, _ = register(client, f"u{i}@example.com", f"Usuaria {i}")
        if i % 2:
            set_plan(uid, "plus")

    plus = client.get("/v1/admin/subscriptions?planId=plus", headers=admin["h"]).json()
    seen, cursor = [], None
    while True:
        url = "/v1/admin/subscriptions?limit=2" + (f"&cursor={cursor}" if cursor else "")
        page = client.get(url, headers=admin["h"]).json()
        seen += [row["uid"] for row in page["items"]]
        cursor = page["nextCursor"]
        if not cursor:
            break

    assert {row["planId"] for row in plus["items"]} == {"plus"} and len(plus["items"]) == 2
    assert all(row["email"].endswith("@example.com") for row in plus["items"])
    assert len(seen) == len(set(seen)) == 5  # 4 usuarias + admin


def test_invalid_subscriptions_cursor(client, admin):
    assert client.get("/v1/admin/subscriptions?cursor=../x", headers=admin["h"]).status_code == 422
