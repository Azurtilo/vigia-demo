"""Alertas de riesgo y de cámara, push con FCM simulado y dispositivos (spec 019, RF-019-04, 05, 09, 14)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from firebase_admin import messaging

from app.core.firebase import get_db
from app.services import alerts, edge_cache, push
from tests.helpers import add_member, register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")

OBSERVATIONS = "/api/v1/edge/observations"
STATUS = "/api/v1/edge/status"


@pytest.fixture
def fcm(monkeypatch):
    """FCM simulado: guarda cada mensaje; `fail` decide qué tokens fallan."""
    sent: list[messaging.Message] = []
    state = {"fail": set(), "unregistered": set()}

    def transport(message):
        if message.token in state["unregistered"]:
            raise messaging.UnregisteredError("token no registrado")
        if message.token in state["fail"]:
            raise ValueError("FCM no disponible")
        sent.append(message)

    monkeypatch.setattr(push, "transport", transport)
    monkeypatch.setattr(push, "enabled", lambda: True)
    edge_cache.forget(everything=True)
    yield sent, state
    edge_cache.forget(everything=True)


def _device(client, headers, name):
    token = f"token-fcm-de-{name}-" + "x" * 20
    body = {"installationId": str(uuid.uuid4()), "enabled": True, "token": token, "platform": "android"}
    assert client.post("/v1/devices", json=body, headers=headers).status_code == 200
    return token


@pytest.fixture
def ctx(client, fcm):
    owner_uid, owner = register(client, "duena@example.com", "Dueña")
    carer_uid, carer = register(client, "cuidadora@example.com", "Cuidadora")
    family_uid, family = register(client, "hijo@example.com", "Hijo")
    viewer_uid, viewer = register(client, "vecina@example.com", "Vecina")
    set_plan(owner_uid, "premium")
    pid = client.post("/v1/patients", json={"displayName": "Abuela Rosa"}, headers=owner).json()["id"]
    add_member(pid, carer_uid, "caregiver")
    add_member(pid, family_uid, "family")
    add_member(pid, viewer_uid, "caregiver", ["patient.view"])  # sin alerts.handle
    get_db().collection("patients").document(pid).collection("consents").document("deteccion").set({"active": True})
    node = client.post(f"/v1/patients/{pid}/nodes", json={"name": "Dormitorio"}, headers=owner).json()
    tokens = {who: _device(client, h, who) for who, h in [("owner", owner), ("carer", carer), ("family", family), ("viewer", viewer)]}
    return {
        "owner": owner, "owner_uid": owner_uid, "carer": carer, "carer_uid": carer_uid, "family": family,
        "viewer": viewer, "pid": pid, "node_id": node["id"], "tokens": tokens,
        "auth": {"Authorization": f"Bearer {node['credential']}"},
    }


def _obs(**overrides):
    return {
        "event_id": str(uuid.uuid4()),
        "observed_at": datetime.now(UTC).isoformat(),
        "posture": "indeterminada",
        "confidence": 0.9,
        "model_version": "pose_landmarker_lite",
        "rule_version": "fall-v1",
        "risk": "fall",
    } | overrides


def _alerts(pid):
    return {s.id: s.to_dict() for s in alerts.alerts_of(pid).stream()}


def _tokens(sent):
    return sorted(m.token for m in sent)


# ---------- Caída: alerta en el mismo lote y push inmediato ----------


def test_a_fall_creates_its_alert_and_pushes_at_once_to_members_with_alerts(client, ctx, fcm):
    sent, _ = fcm

    response = client.post(OBSERVATIONS, json=_obs(), headers=ctx["auth"])

    assert response.status_code == 201
    stored = _alerts(ctx["pid"])
    assert list(stored) == [f"obs_{response.json()['id']}"]
    alert = next(iter(stored.values()))
    assert alert["kind"] == "fall" and alert["pushPending"] is False and alert["pushOutcome"] == "sent"
    tokens = ctx["tokens"]
    assert _tokens(sent) == sorted([tokens["owner"], tokens["carer"], tokens["family"]])  # la vecina no
    message = sent[0]
    assert message.notification.body == push.RISK_TEXT and "Rosa" not in message.notification.body
    assert message.android.priority == "high" and message.android.notification.visibility == "private"


def test_a_retried_fall_neither_duplicates_the_alert_nor_the_push(client, ctx, fcm):
    sent, _ = fcm
    data = _obs()

    client.post(OBSERVATIONS, json=data, headers=ctx["auth"])
    again = client.post(OBSERVATIONS, json=data, headers=ctx["auth"])

    assert again.json()["duplicate"] is True
    assert len(_alerts(ctx["pid"])) == 1 and len(sent) == 3
    alerts.send_pending()
    assert len(sent) == 3


def test_ordinary_observations_create_no_alert(client, ctx, fcm):
    client.post(OBSERVATIONS, json=_obs(posture="supina", risk=""), headers=ctx["auth"])

    assert _alerts(ctx["pid"]) == {} and fcm[0] == []


def test_immobility_alert_is_pushed_by_the_cron_cycle_with_normal_priority(client, ctx, fcm):
    sent, _ = fcm
    client.post(OBSERVATIONS, json=_obs(posture="supina", risk="immobility"), headers=ctx["auth"])
    assert sent == [] and next(iter(_alerts(ctx["pid"]).values()))["pushPending"] is True

    alerts.run_cycle()

    assert len(sent) == 3 and all(m.android.priority is None for m in sent)


def test_without_advanced_alerts_in_the_plan_the_alert_is_kept_but_not_pushed(client, ctx, fcm):
    get_db().collection("plans").document("premium").update({"features.advancedAlerts": False})

    client.post(OBSERVATIONS, json=_obs(), headers=ctx["auth"])

    alert = next(iter(_alerts(ctx["pid"]).values()))
    assert fcm[0] == [] and alert["pushOutcome"] == "not_in_plan"


def test_a_failed_device_is_retried_by_the_cycle_and_the_others_are_not_repeated(client, ctx, fcm):
    sent, state = fcm
    state["fail"].add(ctx["tokens"]["carer"])

    client.post(OBSERVATIONS, json=_obs(), headers=ctx["auth"])
    assert len(sent) == 2 and next(iter(_alerts(ctx["pid"]).values()))["pushPending"] is True

    state["fail"].clear()
    alerts.run_cycle()

    assert _tokens(sent[2:]) == [ctx["tokens"]["carer"]]
    assert next(iter(_alerts(ctx["pid"]).values()))["pushPending"] is False


def test_an_unregistered_token_deactivates_the_device(client, ctx, fcm):
    _, state = fcm
    state["unregistered"].add(ctx["tokens"]["family"])

    client.post(OBSERVATIONS, json=_obs(), headers=ctx["auth"])

    devices = [d.to_dict() for d in get_db().collection("devices").stream()]
    family = [d for d in devices if d["platform"] == "android" and not d["active"]]
    assert len(family) == 1 and family[0]["token"] == ""


def test_with_push_off_the_alert_waits_and_is_sent_when_push_is_turned_on(client, ctx, fcm, monkeypatch):
    sent, _ = fcm
    monkeypatch.setattr(push, "enabled", lambda: False)
    client.post(OBSERVATIONS, json=_obs(), headers=ctx["auth"])
    assert sent == [] and next(iter(_alerts(ctx["pid"]).values()))["pushPending"] is True

    monkeypatch.setattr(push, "enabled", lambda: True)
    alerts.run_cycle()

    assert len(sent) == 3


def test_an_alert_older_than_one_hour_is_not_pushed(client, ctx, fcm, monkeypatch):
    sent, _ = fcm
    monkeypatch.setattr(push, "enabled", lambda: False)
    client.post(OBSERVATIONS, json=_obs(), headers=ctx["auth"])
    alert_id = next(iter(_alerts(ctx["pid"])))
    alerts.alerts_of(ctx["pid"]).document(alert_id).update({"createdAt": datetime.now(UTC) - timedelta(minutes=61)})

    monkeypatch.setattr(push, "enabled", lambda: True)
    alerts.run_cycle()

    assert sent == [] and _alerts(ctx["pid"])[alert_id]["pushOutcome"] == "expired"


def test_a_suspended_account_receives_nothing(client, ctx, fcm):
    sent, _ = fcm
    get_db().collection("users").document(ctx["carer_uid"]).update({"status": "suspended"})

    client.post(OBSERVATIONS, json=_obs(), headers=ctx["auth"])

    assert ctx["tokens"]["carer"] not in _tokens(sent) and len(sent) == 2


# ---------- Cámara ciega y nodo sin señal (ciclo del cron) ----------


def _node(ctx):
    return get_db().collection("edgeNodes").document(ctx["node_id"])


def test_a_silent_node_raises_one_alert_per_episode(client, ctx, fcm):
    sent, _ = fcm
    _node(ctx).update({"lastSeenAt": datetime.now(UTC) - timedelta(minutes=2)})

    first = alerts.run_cycle()
    second = alerts.run_cycle()

    assert first["camera_alerts"] == 1 and second["camera_alerts"] == 0
    alert = next(iter(_alerts(ctx["pid"]).values()))
    assert alert["kind"] == "node_offline"
    assert len(sent) == 3 and sent[0].notification.body == push.MONITOR_TEXT
    assert all(m.android.priority is None for m in sent)


def test_a_blind_camera_raises_an_alert_but_low_light_does_not(client, ctx, fcm):
    client.get(STATUS, params={"monitor_state": "poca_luz"}, headers=ctx["auth"])
    assert alerts.run_cycle()["camera_alerts"] == 0

    client.get(STATUS, params={"monitor_state": "persona_no_visible"}, headers=ctx["auth"])
    assert alerts.run_cycle()["camera_alerts"] == 1

    alert = next(iter(_alerts(ctx["pid"]).values()))
    assert alert["kind"] == "camera_blind" and alert["monitorState"] == "persona_no_visible"


@pytest.mark.parametrize(
    "setup",
    [
        lambda ctx: None,  # nunca se conectó
        lambda ctx: _node(ctx).update({"lastSeenAt": datetime.now(UTC) - timedelta(hours=2)}),  # episodio antiguo
        lambda ctx: (
            _node(ctx).update({"lastSeenAt": datetime.now(UTC) - timedelta(minutes=2)}),
            get_db().collection("patients").document(ctx["pid"]).collection("consents").document("deteccion").set({"active": False}),
        ),
        lambda ctx: (
            _node(ctx).update({"lastSeenAt": datetime.now(UTC) - timedelta(minutes=2)}),
            set_plan(ctx["owner_uid"], "plus"),
        ),
    ],
)
def test_no_camera_alert_without_a_current_episode_or_when_stopped_on_purpose(client, ctx, fcm, setup):
    setup(ctx)

    assert alerts.run_cycle()["camera_alerts"] == 0 and _alerts(ctx["pid"]) == {}


# ---------- Consulta y atención ----------


def test_alerts_are_listed_newest_first_and_attended_once(client, ctx, fcm):
    older = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
    client.post(OBSERVATIONS, json=_obs(observed_at=older), headers=ctx["auth"])
    client.post(OBSERVATIONS, json=_obs(posture="supina", risk="immobility"), headers=ctx["auth"])
    url = f"/v1/patients/{ctx['pid']}/alerts"

    items = client.get(url, headers=ctx["carer"]).json()["items"]
    attended = client.post(f"{url}/{items[1]['id']}/attend", headers=ctx["carer"])
    again = client.post(f"{url}/{items[1]['id']}/attend", headers=ctx["family"])

    assert [i["kind"] for i in items] == ["immobility", "fall"]
    assert attended.json()["status"] == "attended" and attended.json()["attendedBy"] == ctx["carer_uid"]
    assert again.status_code == 409
    assert client.get(url, headers=ctx["viewer"]).status_code == 403


def test_my_alerts_merges_every_patient_with_its_name(client, ctx, fcm):
    other = client.post("/v1/patients", json={"displayName": "Tío Juan"}, headers=ctx["owner"]).json()["id"]
    alerts.alerts_of(other).document("manual").set(
        {"kind": "immobility", "occurredAt": datetime.now(UTC), "status": "open", "pushPending": False}
    )
    client.post(OBSERVATIONS, json=_obs(observed_at=(datetime.now(UTC) - timedelta(seconds=30)).isoformat()), headers=ctx["auth"])

    items = client.get("/v1/me/alerts", headers=ctx["owner"]).json()["items"]
    carer_items = client.get("/v1/me/alerts", headers=ctx["carer"]).json()["items"]

    assert [(i["patientName"], i["kind"]) for i in items] == [("Tío Juan", "immobility"), ("Abuela Rosa", "fall")]
    assert [i["patientName"] for i in carer_items] == ["Abuela Rosa"]  # no es miembro del otro paciente


# ---------- Dispositivos ----------


def test_device_registration_rules(client, ctx):
    installation = str(uuid.uuid4())
    body = {"installationId": installation, "enabled": True, "token": "t" * 30, "platform": "ios"}

    missing = client.post("/v1/devices", json=body | {"token": None}, headers=ctx["owner"])
    ok = client.post("/v1/devices", json=body, headers=ctx["owner"])
    taken = client.post("/v1/devices", json=body, headers=ctx["carer"])
    foreign_off = client.post("/v1/devices", json={"installationId": installation, "enabled": False}, headers=ctx["carer"])
    mode = client.post(
        "/v1/devices/reminder-mode", json={"installationId": installation, "localPostureReminders": True}, headers=ctx["owner"]
    )
    off = client.post("/v1/devices", json={"installationId": installation, "enabled": False}, headers=ctx["owner"])

    assert missing.status_code == 422
    assert ok.json() == {"enabled": True, "deliveryConfigured": True}
    assert taken.status_code == 400 and taken.json()["error"]["code"] == "installation_taken"
    assert foreign_off.json() == {"enabled": False} and mode.json() == {"saved": True}
    assert off.json() == {"enabled": False}
    stored = get_db().collection("devices").document(installation).get().to_dict()
    assert stored["active"] is False and stored["token"] == "" and stored["localPostureReminders"] is True
