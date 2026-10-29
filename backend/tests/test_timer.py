"""Reloj de cambio de posición (HU-04, RF-019-06)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.firebase import get_db
from tests.helpers import add_member, register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")


@pytest.fixture
def ctx(client):
    owner_uid, owner = register(client, "duena@example.com", "Dueña")
    carer_uid, carer = register(client, "cuidadora@example.com", "Cuidadora")
    family_uid, family = register(client, "hijo@example.com", "Hijo")
    set_plan(owner_uid, "plus")
    pid = client.post("/v1/patients", json={"displayName": "Abuela"}, headers=owner).json()["id"]
    add_member(pid, carer_uid, "caregiver")
    add_member(pid, family_uid, "family")
    return {"owner": owner, "owner_uid": owner_uid, "carer": carer, "family": family, "pid": pid}


def _act(client, ctx, action, generation, interval=120, headers=None):
    body = {"action": action, "intervalMinutes": interval, "generation": generation}
    return client.post(f"/v1/patients/{ctx['pid']}/timer", json=body, headers=headers or ctx["carer"])


def _state(client, ctx):
    return client.get(f"/v1/patients/{ctx['pid']}/timer", headers=ctx["family"]).json()


def _position(client, ctx, at=None):
    body = {"position": "left_side"} | ({"at": at} if at else {})
    return client.post(f"/v1/patients/{ctx['pid']}/position-changes", json=body, headers=ctx["carer"])


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_the_clock_is_created_once_and_a_position_change_restarts_it(client, ctx):
    assert _state(client, ctx) == {"exists": False, "paused": False, "generation": 0} | {
        k: None for k in ("intervalMinutes", "anchorAt", "nextDueAt", "lastPositionAt")
    }
    started = _act(client, ctx, "start", 0, 90).json()
    assert started["generation"] == 1 and started["intervalMinutes"] == 90
    assert _act(client, ctx, "start", 0).status_code == 409

    at = (datetime.now(UTC) - timedelta(minutes=5)).replace(microsecond=0)
    _position(client, ctx, at.isoformat())

    state = _state(client, ctx)
    assert _at(state["lastPositionAt"]) == at and _at(state["nextDueAt"]) == at + timedelta(minutes=90)
    assert state["generation"] == 2


def test_a_position_change_never_creates_a_clock(client, ctx):
    _position(client, ctx)

    assert _state(client, ctx)["exists"] is False


def test_a_late_position_change_does_not_move_the_clock_back(client, ctx):
    _act(client, ctx, "start", 0)
    _position(client, ctx)
    before = _state(client, ctx)

    _position(client, ctx, (datetime.now(UTC) - timedelta(hours=1)).isoformat())

    assert _state(client, ctx) == before


def test_a_position_change_task_also_restarts_it(client, ctx):
    _act(client, ctx, "start", 0, 60)
    task = client.post(
        f"/v1/patients/{ctx['pid']}/tasks",
        json={"title": "Cambiar de lado", "kind": "position_change", "scheduleType": "unscheduled", "startDate": "2026-01-01"},
        headers=ctx["owner"],
    ).json()

    client.post(f"/v1/patients/{ctx['pid']}/tasks/{task['id']}/logs", json={"status": "done", "position": "supine"}, headers=ctx["carer"])

    assert _state(client, ctx)["generation"] == 2 and _state(client, ctx)["lastPositionAt"] is not None


def test_pause_resume_and_interval_follow_the_django_rules(client, ctx):
    _act(client, ctx, "start", 0, 120)
    _position(client, ctx)
    last = _at(_state(client, ctx)["lastPositionAt"])

    paused = _act(client, ctx, "pause", 2).json()
    assert paused["paused"] is True and paused["nextDueAt"] is None
    assert _act(client, ctx, "interval", 3, 60).json()["nextDueAt"] is None  # pausado: sin vencimiento
    resumed = _act(client, ctx, "resume", 4, 90).json()
    assert resumed["paused"] is False and resumed["intervalMinutes"] == 90
    assert _act(client, ctx, "resume", 5).status_code == 409

    changed = _act(client, ctx, "interval", 5, 60).json()
    assert _at(changed["nextDueAt"]) == _at(changed["anchorAt"]) + timedelta(minutes=60)
    assert _at(changed["anchorAt"]) == last  # cuenta desde el último cambio de posición


def test_a_stale_generation_or_a_missing_clock_is_a_conflict(client, ctx):
    missing = _act(client, ctx, "pause", 0)
    _act(client, ctx, "start", 0)
    stale = _act(client, ctx, "pause", 7)

    assert missing.json()["error"]["code"] == "timer_missing"
    assert stale.json()["error"]["code"] == "timer_changed"


@pytest.mark.parametrize("interval", [30, 100, 180])
def test_only_60_90_or_120_minutes(client, ctx, interval):
    assert _act(client, ctx, "start", 0, interval).status_code == 422


def test_the_clock_needs_position_changes_in_the_owner_plan(client, ctx):
    set_plan(ctx["owner_uid"], "free")

    response = _act(client, ctx, "start", 0)

    assert response.status_code == 403 and response.json()["error"]["code"] == "plan_feature_unavailable"


def test_the_schedule_goes_to_owner_and_caregivers_without_names(client, ctx):
    _act(client, ctx, "start", 0)

    carer = client.get("/v1/me/timer-schedule", headers=ctx["carer"]).json()
    family = client.get("/v1/me/timer-schedule", headers=ctx["family"]).json()

    assert [i["patientId"] for i in carer["items"]] == [ctx["pid"]] and set(carer["items"][0]) == {"patientId", "generation", "due"}
    assert family["items"] == []

    client.post(f"/v1/patients/{ctx['pid']}/archive", headers=ctx["owner"])
    assert client.get("/v1/me/timer-schedule", headers=ctx["owner"]).json()["items"] == []


def test_a_member_without_care_record_can_see_but_not_change(client, ctx):
    uid, viewer = register(client, "vecina@example.com")
    add_member(ctx["pid"], uid, "caregiver", ["patient.view"])

    assert client.get(f"/v1/patients/{ctx['pid']}/timer", headers=viewer).status_code == 200
    assert _act(client, ctx, "start", 0, headers=viewer).status_code == 403
    assert get_db().collection("patients").document(ctx["pid"]).collection("timer").document("current").get().exists is False
