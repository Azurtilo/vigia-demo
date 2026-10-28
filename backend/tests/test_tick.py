"""Tick del cron y recordatorios por push (RF-019-08, D-088)."""

import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from firebase_admin import messaging

from app.core.config import get_settings
from app.core.firebase import get_db
from app.services import push, reminders
from tests.helpers import add_member, register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")

SANTIAGO = ZoneInfo("America/Santiago")


@pytest.fixture
def fcm(monkeypatch):
    sent: list[messaging.Message] = []
    monkeypatch.setattr(push, "transport", sent.append)
    monkeypatch.setattr(push, "enabled", lambda: True)
    monkeypatch.setattr(reminders, "_last_run", None)
    return sent


def _device(client, headers, name, local_posture=False):
    token = f"token-{name}-" + "x" * 20
    body = {
        "installationId": str(uuid.uuid4()), "enabled": True, "token": token, "platform": "android",
        "localPostureReminders": local_posture,
    }
    client.post("/v1/devices", json=body, headers=headers)
    return token


@pytest.fixture
def ctx(client, fcm):
    owner_uid, owner = register(client, "duena@example.com", "Dueña")
    carer_uid, carer = register(client, "cuidadora@example.com", "Cuidadora")
    family_uid, family = register(client, "hijo@example.com", "Hijo")
    set_plan(owner_uid, "plus")
    pid = client.post("/v1/patients", json={"displayName": "Abuela"}, headers=owner).json()["id"]
    add_member(pid, carer_uid, "caregiver")
    add_member(pid, family_uid, "family")
    tokens = {w: _device(client, h, w) for w, h in [("owner", owner), ("carer", carer), ("family", family)]}
    return {"owner": owner, "carer": carer, "family": family, "pid": pid, "tokens": tokens}


def _med_at(client, ctx, minutes_ago: int) -> tuple[str, datetime]:
    """Medicamento con una toma hace `minutes_ago` minutos (hora local de Santiago)."""
    at = (datetime.now(UTC) - timedelta(minutes=minutes_ago)).replace(second=0, microsecond=0)
    local = at.astimezone(SANTIAGO)
    body = {
        "name": "Paracetamol", "dose": "1 comprimido", "scheduleType": "fixed",
        "schedule": {"times": [local.strftime("%H:%M")]}, "startDate": (local.date() - timedelta(days=1)).isoformat(),
    }
    med_id = client.post(f"/v1/patients/{ctx['pid']}/medications", json=body, headers=ctx["owner"]).json()["id"]
    return med_id, at


# ---------- Tick ----------


@pytest.mark.parametrize(("configured", "sent"), [("", "algo"), ("secreto-del-cron", None), ("secreto-del-cron", "otro")])
def test_the_tick_needs_the_configured_secret(client, monkeypatch, configured, sent):
    monkeypatch.setattr(get_settings(), "cron_secret", configured)
    headers = {"X-Cron-Secret": sent} if sent else {}

    response = client.post("/internal/tick", headers=headers)

    assert response.status_code == 401 and response.json()["error"]["code"] == "cron_unauthorized"


def test_the_tick_runs_alerts_and_reminders(client, ctx, monkeypatch):
    monkeypatch.setattr(get_settings(), "cron_secret", "secreto-del-cron")

    response = client.post("/internal/tick", headers={"X-Cron-Secret": "secreto-del-cron"})

    assert response.status_code == 200
    assert set(response.json()) == {"camera_alerts", "pending_reviewed", "reminders_sent", "purge"}


# ---------- Tomas ----------


def test_an_unrecorded_dose_is_reminded_once_to_owner_and_caregiver(client, ctx, fcm):
    _med_at(client, ctx, 20)

    first = reminders.run(force=True)
    second = reminders.run(force=True)

    assert (first, second) == (1, 0)
    assert sorted(m.token for m in fcm) == sorted([ctx["tokens"]["owner"], ctx["tokens"]["carer"]])  # la familia no
    assert fcm[0].notification.body == reminders.CARE_TEXT


def test_a_recorded_dose_is_not_reminded(client, ctx, fcm):
    med_id, at = _med_at(client, ctx, 20)
    client.post(
        f"/v1/patients/{ctx['pid']}/medications/{med_id}/doses",
        json={"status": "given", "scheduledAt": at.isoformat()},
        headers=ctx["carer"],
    )

    assert reminders.run(force=True) == 0 and fcm == []


def test_a_dose_older_than_one_hour_is_not_reminded(client, ctx, fcm):
    _med_at(client, ctx, 90)

    assert reminders.run(force=True) == 0 and fcm == []


def test_the_reminder_key_matches_the_dose_log_id(client, ctx, fcm):
    med_id, at = _med_at(client, ctx, 10)

    reminders.run(force=True)

    marker = f"{ctx['pid']}_{med_id}_{at.strftime('%Y%m%dT%H%MZ')}"
    assert get_db().collection("reminderDeliveries").document(marker).get().exists


def test_reminders_run_at_most_every_5_minutes(client, ctx, fcm):
    now = datetime.now(UTC)
    reminders.run(now)
    _med_at(client, ctx, 10)

    assert reminders.run(now + timedelta(minutes=1)) == 0
    assert reminders.run(now + timedelta(minutes=5)) == 1


# ---------- Reloj de posición ----------


def _timer_due_in(client, ctx, minutes: int) -> None:
    body = {"action": "start", "intervalMinutes": 60, "generation": 0}
    client.post(f"/v1/patients/{ctx['pid']}/timer", json=body, headers=ctx["carer"])
    ref = get_db().collection("patients").document(ctx["pid"]).collection("timer").document("current")
    ref.update({"nextDueAt": datetime.now(UTC) + timedelta(minutes=minutes)})


def test_a_clock_due_soon_is_reminded_except_on_phones_that_schedule_it(client, ctx, fcm):
    local_phone = _device(client, ctx["carer"], "carer-2", local_posture=True)
    _timer_due_in(client, ctx, 5)

    assert reminders.run(force=True) == 1

    tokens = [m.token for m in fcm]
    assert ctx["tokens"]["carer"] in tokens and ctx["tokens"]["owner"] in tokens
    assert local_phone not in tokens and ctx["tokens"]["family"] not in tokens


def test_a_clock_far_from_due_is_not_reminded(client, ctx, fcm):
    _timer_due_in(client, ctx, 30)

    assert reminders.run(force=True) == 0
