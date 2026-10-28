"""Nodos de detección, contrato Edge y observaciones (spec 019, RF-019-02, 03, 05, 10, 11).

El contrato Edge debe comportarse igual que la API Django: el nodo no cambia (D-086).
"""

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.firebase import get_db
from app.services import edge_cache
from tests.helpers import add_member, register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")

STATUS = "/api/v1/edge/status"
OBSERVATIONS = "/api/v1/edge/observations"


@pytest.fixture(autouse=True)
def _empty_cache():
    edge_cache.forget(everything=True)
    yield
    edge_cache.forget(everything=True)


def _consent(pid: str, active: bool = True) -> None:
    get_db().collection("patients").document(pid).collection("consents").document("deteccion").set({"active": active})


@pytest.fixture
def ctx(client):
    owner_uid, owner = register(client, "duena@example.com", "Dueña")
    carer_uid, carer = register(client, "cuidadora@example.com", "Cuidadora")
    family_uid, family = register(client, "hijo@example.com", "Hijo")
    set_plan(owner_uid, "premium")
    pid = client.post("/v1/patients", json={"displayName": "Abuela"}, headers=owner).json()["id"]
    add_member(pid, carer_uid, "caregiver")
    add_member(pid, family_uid, "family")
    _consent(pid)
    return {"owner": owner, "owner_uid": owner_uid, "carer": carer, "family": family, "pid": pid}


def _link(client, ctx, name="Cámara del dormitorio"):
    return client.post(f"/v1/patients/{ctx['pid']}/nodes", json={"name": name}, headers=ctx["owner"])


@pytest.fixture
def node(client, ctx):
    created = _link(client, ctx).json()
    return {"id": created["id"], "auth": {"Authorization": f"Bearer {created['credential']}"}}


def _obs(**overrides) -> dict:
    data = {
        "event_id": str(uuid.uuid4()),
        "observed_at": datetime.now(UTC).isoformat(),
        "posture": "supina",
        "confidence": 0.91,
        "model_version": "pose_landmarker_lite",
        "rule_version": "posture-v1",
        "risk": "",
    }
    return data | overrides


def _send(client, node, data) -> object:
    return client.post(OBSERVATIONS, json=data, headers=node["auth"])


def _code(response):
    return response.json()["error"]["code"]


# ---------- Vincular y revocar ----------


def test_link_returns_the_token_once_and_stores_only_its_hash(client, ctx):
    response = _link(client, ctx)

    assert response.status_code == 201
    body = response.json()
    stored = get_db().collection("edgeNodes").document(body["id"]).get().to_dict()
    assert stored["credentialHash"] == hashlib.sha256(body["credential"].encode()).hexdigest()
    assert body["credential"] not in json.dumps(stored, default=str)
    listed = client.get(f"/v1/patients/{ctx['pid']}/nodes", headers=ctx["owner"]).json()["items"]
    assert [n["name"] for n in listed] == ["Cámara del dormitorio"] and "credential" not in listed[0]


@pytest.mark.parametrize("who", ["carer", "family"])
def test_only_the_owner_manages_nodes(client, ctx, who):
    response = client.post(f"/v1/patients/{ctx['pid']}/nodes", json={"name": "X"}, headers=ctx[who])

    assert response.status_code == 403 and _code(response) == "owner_only"
    assert client.get(f"/v1/patients/{ctx['pid']}/nodes", headers=ctx[who]).status_code == 403


def test_link_requires_cameras_in_the_owner_plan(client, ctx):
    set_plan(ctx["owner_uid"], "plus")

    response = _link(client, ctx)

    assert response.status_code == 403 and _code(response) == "plan_feature_unavailable"


def test_link_requires_detection_consent(client, ctx):
    _consent(ctx["pid"], active=False)

    response = _link(client, ctx)

    assert response.status_code == 403 and _code(response) == "consent_required"


def test_one_active_node_per_patient_until_revoked(client, ctx, node):
    second = _link(client, ctx, "Otra")
    assert second.status_code == 409 and _code(second) == "node_already_active"

    assert client.post(f"/v1/nodes/{node['id']}/revoke", headers=ctx["owner"]).json() == {"revoked": True}

    assert _link(client, ctx, "Otra").status_code == 201


def test_blank_name_is_rejected(client, ctx):
    assert _link(client, ctx, "   ").status_code == 422


# ---------- Renovación (GET /api/v1/edge/status) ----------


def test_status_grants_a_lease_without_caching(client, node):
    response = client.get(STATUS, params={"monitor_state": "normal"}, headers=node["auth"])

    assert response.status_code == 200
    assert response.json()["enabled"] is True and response.json()["lease_seconds"] == 30
    assert response.headers["Cache-Control"] == "no-store, private"


def test_status_stores_the_monitor_state_when_it_changes(client, node):
    client.get(STATUS, params={"monitor_state": "normal"}, headers=node["auth"])
    client.get(STATUS, params={"monitor_state": "poca_luz"}, headers=node["auth"])

    stored = get_db().collection("edgeNodes").document(node["id"]).get().to_dict()
    assert stored["monitorState"] == "poca_luz" and stored["lastSeenAt"] is not None


@pytest.mark.parametrize(
    "params",
    [{"monitor_state": "dormido"}, {"monitor_state": ["normal", "poca_luz"]}, {"otro": "1"}],
)
def test_status_rejects_unknown_parameters(client, node, params):
    response = client.get(STATUS, params=params, headers=node["auth"])

    assert response.status_code == 400


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer otro-token"}, {"Authorization": "Token abc"}, {"Authorization": "Bearer " + "a" * 130}],
)
def test_status_without_a_valid_token_is_401(client, node, headers):
    assert client.get(STATUS, headers=headers).status_code == 401


def test_revocation_stops_the_node_at_once_despite_the_cache(client, ctx, node):
    assert client.get(STATUS, headers=node["auth"]).status_code == 200

    client.post(f"/v1/nodes/{node['id']}/revoke", headers=ctx["owner"])

    assert client.get(STATUS, headers=node["auth"]).status_code == 401
    assert _send(client, node, _obs()).status_code == 401


def test_downgrade_stops_the_node_at_once_despite_the_cache(client, ctx, node):
    assert client.get(STATUS, headers=node["auth"]).status_code == 200

    changed = client.post("/v1/me/subscription/change", json={"planId": "plus"}, headers=ctx["owner"])

    assert changed.status_code == 200
    response = client.get(STATUS, headers=node["auth"])
    assert response.status_code == 403 and _code(response) == "monitoring_inactive"


def test_archiving_the_patient_stops_the_node(client, ctx, node):
    assert client.get(STATUS, headers=node["auth"]).status_code == 200

    client.post(f"/v1/patients/{ctx['pid']}/archive", headers=ctx["owner"])

    assert client.get(STATUS, headers=node["auth"]).status_code == 403


def test_without_detection_consent_the_node_gets_403(client, ctx, node):
    _consent(ctx["pid"], active=False)

    assert client.get(STATUS, headers=node["auth"]).status_code == 403


# ---------- Observaciones (POST /api/v1/edge/observations) ----------


def test_observation_is_stored_once_and_retries_are_duplicates(client, ctx, node):
    data = _obs()

    first = _send(client, node, data)
    again = _send(client, node, data)
    changed = _send(client, node, data | {"confidence": 0.5})

    assert first.status_code == 201 and first.json()["duplicate"] is False
    assert again.status_code == 200 and again.json() == {"id": first.json()["id"], "duplicate": True}
    assert changed.status_code == 409


def test_a_late_fall_keeps_its_original_time(client, ctx, node):
    observed = datetime.now(UTC) - timedelta(minutes=30)

    response = _send(client, node, _obs(observed_at=observed.isoformat(), risk="fall", posture="indeterminada"))

    assert response.status_code == 201
    stored = get_db().collection("patients").document(ctx["pid"]).collection("observations")
    row = stored.document(response.json()["id"]).get().to_dict()
    assert row["observedAt"] == observed and row["risk"] == "fall" and row["sourceType"] == "fixed"


def _now(delta: timedelta = timedelta()) -> str:
    return (datetime.now(UTC) + delta).isoformat()


# Funciones: la hora se calcula al ejecutar cada caso, no al cargar el archivo.
@pytest.mark.parametrize(
    "make",
    [
        lambda: _obs() | {"image": "AAAA"},  # nunca imágenes ni claves extra
        lambda: {k: v for k, v in _obs().items() if k != "risk"},
        lambda: _obs(event_id="no-es-uuid"),
        lambda: _obs(observed_at="2026-01-15T12:00:00"),  # sin zona horaria
        lambda: _obs(observed_at="ayer"),
        lambda: _obs(observed_at=_now(-timedelta(minutes=3))),  # común vencida
        lambda: _obs(observed_at=_now(-timedelta(hours=2)), risk="fall"),  # riesgo vencido
        lambda: _obs(observed_at=_now(timedelta(minutes=1))),  # reloj adelantado
        lambda: _obs(confidence=1.5),
        lambda: _obs(confidence=True),
        lambda: _obs(confidence="NaN"),
        lambda: _obs(posture="sentada"),
        lambda: _obs(risk="sleep"),
        lambda: _obs(risk=["fall"]),
        lambda: _obs(posture="indeterminada", risk="immobility"),
        lambda: _obs(model_version=""),
        lambda: _obs(rule_version="v" * 81),
        lambda: ["no", "es", "objeto"],
    ],
)
def test_invalid_observations_are_400_so_the_node_drops_them(client, node, make):
    response = _send(client, node, make())

    assert response.status_code == 400 and response.headers["Cache-Control"] == "no-store, private"


def test_body_must_be_json_and_at_most_4_kb(client, node):
    as_text = client.post(OBSERVATIONS, content=json.dumps(_obs()), headers={**node["auth"], "Content-Type": "text/plain"})
    too_big = client.post(OBSERVATIONS, content=b"{" + b" " * 4100 + b"}", headers={**node["auth"], "Content-Type": "application/json"})
    broken = client.post(OBSERVATIONS, content=b"{no json", headers={**node["auth"], "Content-Type": "application/json"})

    assert (as_text.status_code, too_big.status_code, broken.status_code) == (400, 400, 400)


def test_risk_combinations_accepted_like_django(client, node):
    fall = _send(client, node, _obs(posture="indeterminada", risk="fall"))
    immobility = _send(client, node, _obs(posture="lateral-izquierda", risk="immobility"))

    assert (fall.status_code, immobility.status_code) == (201, 201)


# ---------- Consulta, estado de la cámara y teléfono ----------


def test_members_with_alerts_permission_list_observations_newest_first(client, ctx, node):
    older = _now(-timedelta(seconds=60))
    _send(client, node, _obs(observed_at=older))
    _send(client, node, _obs(posture="lateral-derecha"))

    page = client.get(f"/v1/patients/{ctx['pid']}/observations", headers=ctx["carer"]).json()

    assert [i["posture"] for i in page["items"]] == ["lateral-derecha", "supina"]
    assert page["items"][0]["source"] == "Cámara del dormitorio" and page["enabled"] is True
    assert page["nextCursor"] is None


def test_observations_require_alerts_permission(client, ctx, node):
    uid, headers = register(client, "otra@example.com")
    add_member(ctx["pid"], uid, "caregiver", ["patient.view"])

    assert client.get(f"/v1/patients/{ctx['pid']}/observations", headers=headers).status_code == 403


def test_observations_paginate_by_30(client, ctx, node):
    base = datetime.now(UTC) - timedelta(seconds=90)
    for i in range(31):
        _send(client, node, _obs(observed_at=(base + timedelta(seconds=i)).isoformat()))
    url = f"/v1/patients/{ctx['pid']}/observations"

    first = client.get(url, headers=ctx["owner"]).json()
    second = client.get(url, params={"cursor": first["nextCursor"]}, headers=ctx["owner"]).json()

    assert len(first["items"]) == 30 and len(second["items"]) == 1 and second["nextCursor"] is None


def test_camera_state_is_read_only_for_every_member(client, ctx, node):
    url = f"/v1/patients/{ctx['pid']}/camera"
    assert client.get(url, headers=ctx["carer"]).json() == {"state": "sin_senal"}  # nunca se conectó

    client.get(STATUS, params={"monitor_state": "persona_no_visible"}, headers=node["auth"])

    for who in ("owner", "family", "carer"):
        assert client.get(url, headers=ctx[who]).json() == {"state": "persona_no_visible"}


def test_camera_state_is_null_without_nodes_or_without_cameras_in_the_plan(client, ctx, node):
    url = f"/v1/patients/{ctx['pid']}/camera"
    client.get(STATUS, params={"monitor_state": "normal"}, headers=node["auth"])
    assert client.get(url, headers=ctx["owner"]).json() == {"state": "normal"}

    set_plan(ctx["owner_uid"], "plus")

    assert client.get(url, headers=ctx["owner"]).json() == {"state": None}


def _phone(**overrides) -> dict:
    data = _obs()
    data.pop("risk")
    return data | {"platform": "android"} | overrides


def test_phone_snapshot_is_recorded_by_the_caregiver(client, ctx):
    url = f"/v1/patients/{ctx['pid']}/phone-observations"
    data = _phone()

    status_ = client.get(url, headers=ctx["carer"])
    first = client.post(url, json=data, headers=ctx["carer"])
    again = client.post(url, json=data, headers=ctx["carer"])

    assert status_.json()["mode"] == "snapshot"
    assert first.status_code == 201 and first.json()["sourceType"] == "phone"
    assert again.status_code == 200 and again.json()["duplicate"] is True


@pytest.mark.parametrize(
    "make",
    [
        lambda: _phone(platform="windows"),
        lambda: _phone() | {"risk": "fall"},
        lambda: _phone(observed_at=_now(-timedelta(minutes=3))),
    ],
)
def test_phone_snapshot_keeps_the_django_contract(client, ctx, make):
    response = client.post(f"/v1/patients/{ctx['pid']}/phone-observations", json=make(), headers=ctx["carer"])

    assert response.status_code == 400


def test_phone_snapshot_requires_consent(client, ctx):
    _consent(ctx["pid"], active=False)

    response = client.post(f"/v1/patients/{ctx['pid']}/phone-observations", json=_phone(), headers=ctx["carer"])

    assert response.status_code == 403 and _code(response) == "consent_required"
