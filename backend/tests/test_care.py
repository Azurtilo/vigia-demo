"""Plan de cuidados: tareas, cambios de posición, funciones según el plan y agenda combinada."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.care import TaskLogCreate
from app.services import care as care_service
from tests.helpers import add_member, register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")

DAY = "2026-01-15"
AT_09 = "2026-01-15T12:00:00Z"  # 09:00 en Santiago (verano, UTC-3)


@pytest.fixture
def ctx(client):
    owner_uid, owner = register(client, "duena@example.com", "Dueña")
    carer_uid, carer = register(client, "cuidadora@example.com", "Cuidadora")
    pid = client.post("/v1/patients", json={"displayName": "Abuela"}, headers=owner).json()["id"]
    add_member(pid, carer_uid, "caregiver")
    return {"owner": owner, "owner_uid": owner_uid, "carer": carer, "carer_uid": carer_uid, "pid": pid}


def _task(client, ctx, headers=None, **overrides):
    body = {"title": "Hidratar", "scheduleType": "fixed", "schedule": {"times": ["09:00"]}, "startDate": "2026-01-01", **overrides}
    return client.post(f"/v1/patients/{ctx['pid']}/tasks", json=body, headers=headers or ctx["owner"])


def _log(client, ctx, task_id, headers=None, **body):
    return client.post(f"/v1/patients/{ctx['pid']}/tasks/{task_id}/logs", json=body, headers=headers or ctx["carer"])


def _position(client, ctx, headers=None, **body):
    return client.post(f"/v1/patients/{ctx['pid']}/position-changes", json=body, headers=headers or ctx["carer"])


def _agenda(client, ctx, day=DAY):
    return client.get(f"/v1/patients/{ctx['pid']}/agenda?date={day}", headers=ctx["owner"]).json()


def _code(response):
    return response.json()["error"]["code"]


# ---------- Plan Gratis: lo básico ----------


def test_free_plan_creates_and_completes_basic_tasks(client, ctx):
    task_id = _task(client, ctx).json()["id"]

    done = _log(client, ctx, task_id, status="done", scheduledAt=AT_09, doneAt="2026-01-15T12:10:00Z")

    assert done.status_code == 201 and done.json()["recordedBy"] == ctx["carer_uid"]
    items = _agenda(client, ctx)["items"]
    assert [(i["kind"], i["title"], i["localTime"], i["status"]) for i in items] == [("task", "Hidratar", "09:00", "done")]


def test_same_task_occurrence_cannot_be_recorded_twice(client, ctx):
    task_id = _task(client, ctx).json()["id"]
    _log(client, ctx, task_id, status="done", scheduledAt=AT_09)

    again = _log(client, ctx, task_id, headers=ctx["owner"], status="done", scheduledAt=AT_09)

    assert again.status_code == 409 and _code(again) == "task_already_recorded"


@pytest.mark.parametrize(
    ("action", "what"),
    [
        (lambda c, x: _task(c, x, kind="position_change"), "tarea de posición"),
        (lambda c, x: _task(c, x, assignedTo=x["carer_uid"]), "asignar responsable"),
        (lambda c, x: _log(c, x, _task(c, x).json()["id"], status="skipped", scheduledAt=AT_09, reason="Dormía"), "no realizada"),
        (lambda c, x: _log(c, x, _task(c, x).json()["id"], status="done", scheduledAt=AT_09, note="Tomó poco"), "observación"),
        (lambda c, x: _position(c, x, position="left_side"), "cambio de posición"),
    ],
)
def test_free_plan_blocks_extended_features(client, ctx, action, what):
    response = action(client, ctx)

    assert response.status_code == 403, what
    assert _code(response) == "plan_feature_unavailable"
    assert "plan del responsable" in response.json()["error"]["message"]


# ---------- Plus: seguimiento ampliado y posiciones ----------


def test_plus_plan_enables_extended_tracking(client, ctx):
    set_plan(ctx["owner_uid"], "plus")
    task_id = _task(client, ctx, assignedTo=ctx["carer_uid"]).json()["id"]

    skipped = _log(client, ctx, task_id, status="skipped", scheduledAt=AT_09, reason="Estaba durmiendo", note="Reintentar 10:00")

    assert skipped.status_code == 201
    assert skipped.json()["doneAt"] is None and skipped.json()["note"] == "Reintentar 10:00"
    item = _agenda(client, ctx)["items"][0]
    assert item["assignedTo"] == ctx["carer_uid"] and item["status"] == "skipped"


def test_assignee_must_be_a_member(client, ctx):
    set_plan(ctx["owner_uid"], "plus")
    stranger_uid, _ = register(client, "extrana@example.com")

    assert _code(_task(client, ctx, assignedTo=stranger_uid)) == "assignee_not_member"


def test_position_change_task_requires_position(client, ctx):
    set_plan(ctx["owner_uid"], "plus")
    task_id = _task(client, ctx, title="Cambio de posición", kind="position_change", schedule={"times": ["09:00", "13:00"]}).json()["id"]

    missing = _log(client, ctx, task_id, status="done", scheduledAt=AT_09)
    ok = _log(client, ctx, task_id, status="done", scheduledAt=AT_09, position="left_side")

    assert _code(missing) == "position_required"
    assert ok.status_code == 201 and ok.json()["position"] == "left_side"
    types = [d.get("type") for d in get_db().collection(f"patients/{ctx['pid']}/activity").stream()]
    assert "position.changed" in types


def test_general_task_rejects_position(client, ctx):
    set_plan(ctx["owner_uid"], "plus")
    task_id = _task(client, ctx).json()["id"]

    assert _code(_log(client, ctx, task_id, status="done", scheduledAt=AT_09, position="prone")) == "position_not_allowed"


def test_ad_hoc_position_change(client, ctx):
    set_plan(ctx["owner_uid"], "plus")

    other_missing = _position(client, ctx, position="other")
    ok = _position(client, ctx, position="other", positionOther="Semisentada 45°", at="2026-01-15T18:00:00Z")

    assert other_missing.status_code == 422
    assert ok.status_code == 201 and ok.json()["taskId"] is None
    item = _agenda(client, ctx)["items"][0]
    assert (item["kind"], item["taskId"], item["taskKind"], item["status"]) == ("task", None, "position_change", "done")


def test_agenda_reports_owner_plan_features(client, ctx):
    free = _agenda(client, ctx)["features"]
    set_plan(ctx["owner_uid"], "plus")
    plus = client.get(f"/v1/patients/{ctx['pid']}/agenda?date={DAY}", headers=ctx["carer"]).json()["features"]

    assert free == {"extendedCareTracking": False, "positionChanges": False}
    assert plus == {"extendedCareTracking": True, "positionChanges": True}  # aunque la cuidadora tenga Gratis


def test_owner_plan_applies_to_caregiver_regardless_of_own_plan(client, ctx):
    """La cuidadora tiene plan Gratis, pero el paciente es de una dueña con Plus."""
    set_plan(ctx["owner_uid"], "plus")

    assert _position(client, ctx, position="supine").status_code == 201


def test_downgrade_keeps_existing_tasks_but_blocks_extended_actions(client, ctx):
    set_plan(ctx["owner_uid"], "plus")
    task_id = _task(client, ctx, assignedTo=ctx["carer_uid"]).json()["id"]
    set_plan(ctx["owner_uid"], "free")

    tasks = client.get(f"/v1/patients/{ctx['pid']}/tasks", headers=ctx["owner"]).json()
    skipped = _log(client, ctx, task_id, status="skipped", scheduledAt=AT_09, reason="x")
    done = _log(client, ctx, task_id, status="done", scheduledAt=AT_09)

    assert tasks[0]["assignedTo"] == ctx["carer_uid"]  # no se borra nada
    assert _code(skipped) == "plan_feature_unavailable"
    assert done.status_code == 201


# ---------- Reglas de registro ----------


@pytest.mark.parametrize(
    ("payload", "code_or_status"),
    [
        ({"status": "done", "scheduledAt": "2026-01-15T13:00:00Z"}, "not_scheduled"),
        ({"status": "done"}, "scheduled_at_required"),
        ({"status": "done", "scheduledAt": AT_09, "doneAt": "2999-01-01T00:00:00Z"}, "future_time"),
        ({"status": "skipped", "scheduledAt": AT_09}, 422),  # sin motivo
        ({"status": "hecha", "scheduledAt": AT_09}, 422),
    ],
)
def test_task_log_rules(client, ctx, payload, code_or_status):
    set_plan(ctx["owner_uid"], "plus")
    task_id = _task(client, ctx).json()["id"]

    response = _log(client, ctx, task_id, **payload)

    if isinstance(code_or_status, int):
        assert response.status_code == code_or_status
    else:
        assert _code(response) == code_or_status


def test_unscheduled_task(client, ctx):
    task_id = _task(client, ctx, title="Cambio de sábanas", scheduleType="unscheduled", schedule=None).json()["id"]

    first = _log(client, ctx, task_id, status="done", doneAt="2026-01-15T14:00:00Z")
    second = _log(client, ctx, task_id, status="done", doneAt="2026-01-15T20:00:00Z")
    with_time = _log(client, ctx, task_id, status="done", scheduledAt=AT_09)

    assert first.status_code == second.status_code == 201
    assert _code(with_time) == "schedule_not_allowed"
    assert len(_agenda(client, ctx)["items"]) == 2


def test_permissions(client, ctx):
    viewer_uid, viewer = register(client, "solo-mira@example.com")
    add_member(ctx["pid"], viewer_uid, "caregiver", ["patient.view"])
    task_id = _task(client, ctx).json()["id"]

    assert _code(_task(client, ctx, headers=ctx["carer"])) == "forbidden"  # cuidadora sin care.manage
    assert _code(_log(client, ctx, task_id, headers=viewer, status="done", scheduledAt=AT_09)) == "forbidden"


def test_archived_patient_tasks_are_read_only(client, ctx):
    client.post(f"/v1/patients/{ctx['pid']}/archive", headers=ctx["owner"])

    assert _code(_task(client, ctx)) == "patient_archived"


def test_simultaneous_records_of_same_occurrence_create_at_most_one(client, ctx):
    task_id = _task(client, ctx).json()["id"]
    body = TaskLogCreate(status="done", scheduled_at=datetime.fromisoformat(AT_09))

    def attempt(uid):
        try:
            care_service.log_task(ctx["pid"], uid, task_id, body)
            return "ok"
        except AppError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(attempt, [ctx["owner_uid"], ctx["carer_uid"]] * 2))

    assert results.count("ok") <= 1, results
    assert set(results) <= {"ok", "task_already_recorded", "service_busy"}, results
    assert len(get_db().collection(f"patients/{ctx['pid']}/taskLogs").get()) == results.count("ok")


# ---------- Correcciones ----------


def test_corrections(client, ctx):
    set_plan(ctx["owner_uid"], "plus")
    other_uid, other = register(client, "otra@example.com")
    add_member(ctx["pid"], other_uid, "caregiver")
    task_id = _task(client, ctx).json()["id"]
    log_id = _log(client, ctx, task_id, status="done", scheduledAt=AT_09).json()["id"]
    url = f"/v1/patients/{ctx['pid']}/task-logs/{log_id}"

    by_other = client.patch(url, json={"status": "skipped", "reason": "x"}, headers=other)
    by_author = client.patch(url, json={"status": "skipped", "reason": "Me equivoqué"}, headers=ctx["carer"])

    assert _code(by_other) == "forbidden"
    assert by_author.json()["status"] == "skipped" and by_author.json()["corrections"] == 1
    stored = get_db().document(f"patients/{ctx['pid']}/taskLogs/{log_id}").get().to_dict()
    assert stored["history"][0]["status"] == "done"


def test_correction_respects_plan(client, ctx):
    task_id = _task(client, ctx).json()["id"]
    log_id = _log(client, ctx, task_id, status="done", scheduledAt=AT_09).json()["id"]

    response = client.patch(
        f"/v1/patients/{ctx['pid']}/task-logs/{log_id}", json={"status": "skipped", "reason": "x"}, headers=ctx["carer"]
    )

    assert _code(response) == "plan_feature_unavailable"


# ---------- Agenda combinada ----------


def test_agenda_merges_medications_and_tasks_in_time_order(client, ctx):
    client.post(
        f"/v1/patients/{ctx['pid']}/medications",
        json={"name": "Paracetamol", "dose": "1 comprimido", "scheduleType": "fixed",
              "schedule": {"times": ["08:00"]}, "startDate": "2026-01-01"},
        headers=ctx["owner"],
    )
    _task(client, ctx, title="Hidratar", schedule={"times": ["09:00", "07:00"]})

    items = _agenda(client, ctx)["items"]

    assert [(i["kind"], i["localTime"]) for i in items] == [("task", "07:00"), ("medication", "08:00"), ("task", "09:00")]
