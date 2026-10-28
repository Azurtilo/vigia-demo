"""Medicamentos, agenda y registro de tomas.

Se usan fechas pasadas fijas (enero de 2026) para que las pruebas no dependan del día en que corren.
"""

from concurrent.futures import ThreadPoolExecutor

import pytest
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.medication import DoseLogCreate
from app.services import medications as meds_service
from tests.helpers import add_member, register

pytestmark = pytest.mark.usefixtures("seeded_plans")

DAY = "2026-01-15"  # jueves; en Santiago es horario de verano (UTC-3)
AT_08 = "2026-01-15T11:00:00Z"  # 08:00 local
AT_20 = "2026-01-15T23:00:00Z"  # 20:00 local


@pytest.fixture
def ctx(client):
    owner_uid, owner = register(client, "duena@example.com", "Dueña")
    carer_uid, carer = register(client, "cuidadora@example.com", "Cuidadora")
    pid = client.post("/v1/patients", json={"displayName": "Abuela"}, headers=owner).json()["id"]
    add_member(pid, carer_uid, "caregiver")
    return {"owner": owner, "owner_uid": owner_uid, "carer": carer, "carer_uid": carer_uid, "pid": pid}


def _med(client, ctx, headers=None, **overrides):
    body = {
        "name": "Paracetamol",
        "dose": "1 comprimido de 500 mg",
        "instructions": "Con comida",
        "scheduleType": "fixed",
        "schedule": {"times": ["20:00", "08:00"]},
        "startDate": "2026-01-01",
        **overrides,
    }
    return client.post(f"/v1/patients/{ctx['pid']}/medications", json=body, headers=headers or ctx["owner"])


def _dose(client, ctx, med_id, headers=None, **body):
    return client.post(f"/v1/patients/{ctx['pid']}/medications/{med_id}/doses", json=body, headers=headers or ctx["carer"])


def _agenda(client, ctx, day=DAY, headers=None):
    return client.get(f"/v1/patients/{ctx['pid']}/agenda?date={day}", headers=headers or ctx["owner"]).json()


# ---------- Medicamentos ----------


def test_create_medication_as_prescribed(client, ctx):
    response = _med(client, ctx)

    body = response.json()
    assert response.status_code == 201
    assert body["dose"] == "1 comprimido de 500 mg"  # texto tal cual, sin interpretar
    assert body["schedule"] == {"times": ["08:00", "20:00"], "daysOfWeek": []}
    assert body["active"] is True and body["createdBy"] == ctx["owner_uid"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"schedule": None},  # horario fijo sin horas
        {"scheduleType": "as_needed"},  # "si es necesario" con horario
        {"dose": ""},
        {"endDate": "2025-12-31"},  # término antes del inicio
        {"schedule": {"times": ["8am"]}},
        {"frequencyHours": 8},  # campo inventado
    ],
)
def test_invalid_medications_are_rejected(client, ctx, overrides):
    assert _med(client, ctx, **overrides).status_code == 422


def test_caregiver_cannot_manage_medications_and_stranger_cannot_see_them(client, ctx):
    _, stranger = register(client, "extrana@example.com")
    med_id = _med(client, ctx).json()["id"]

    assert _med(client, ctx, headers=ctx["carer"]).json()["error"]["code"] == "forbidden"
    assert client.patch(f"/v1/patients/{ctx['pid']}/medications/{med_id}", json={"dose": "2"}, headers=ctx["carer"]).status_code == 403
    assert client.get(f"/v1/patients/{ctx['pid']}/medications", headers=ctx["carer"]).status_code == 200
    assert client.get(f"/v1/patients/{ctx['pid']}/medications", headers=stranger).status_code == 404


def test_update_keeps_previous_version(client, ctx):
    med_id = _med(client, ctx).json()["id"]

    response = client.patch(
        f"/v1/patients/{ctx['pid']}/medications/{med_id}", json={"dose": "1/2 comprimido"}, headers=ctx["owner"]
    )

    revisions = [r.to_dict() for r in get_db().document(f"patients/{ctx['pid']}/medications/{med_id}").collection("revisions").stream()]
    assert response.json()["dose"] == "1/2 comprimido"
    assert len(revisions) == 1
    assert revisions[0]["previous"]["dose"] == "1 comprimido de 500 mg"
    assert revisions[0]["changedBy"] == ctx["owner_uid"] and revisions[0]["fields"] == ["dose"]


def test_update_rejects_inconsistent_result(client, ctx):
    med_id = _med(client, ctx).json()["id"]
    url = f"/v1/patients/{ctx['pid']}/medications/{med_id}"

    assert client.patch(url, json={"schedule": None}, headers=ctx["owner"]).json()["error"]["code"] == "schedule_required"
    assert client.patch(url, json={"endDate": "2025-01-01"}, headers=ctx["owner"]).json()["error"]["code"] == "invalid_dates"
    assert client.patch(url, json={"name": None}, headers=ctx["owner"]).status_code == 422
    # Pasar a "si es necesario" quita el horario automáticamente.
    assert client.patch(url, json={"scheduleType": "as_needed"}, headers=ctx["owner"]).json()["schedule"] is None


def test_archived_patient_medications_are_read_only(client, ctx):
    client.post(f"/v1/patients/{ctx['pid']}/archive", headers=ctx["owner"])

    assert _med(client, ctx).json()["error"]["code"] == "patient_archived"


# ---------- Agenda ----------


def test_agenda_lists_scheduled_doses_in_patient_local_time(client, ctx):
    med_id = _med(client, ctx).json()["id"]

    agenda = _agenda(client, ctx)

    assert agenda["timeZone"] == "America/Santiago"
    assert [(i["localTime"], i["scheduledAt"], i["status"]) for i in agenda["items"]] == [
        ("08:00", AT_08, "pending"),
        ("20:00", AT_20, "pending"),
    ]
    assert {i["medicationId"] for i in agenda["items"]} == {med_id}


def test_agenda_respects_dates_days_and_active(client, ctx):
    _med(client, ctx, schedule={"times": ["09:00"], "daysOfWeek": [1]}, startDate="2026-01-05", endDate="2026-01-31")

    assert len(_agenda(client, ctx, "2026-01-12")["items"]) == 1  # lunes
    assert _agenda(client, ctx, "2026-01-13")["items"] == []  # martes
    assert _agenda(client, ctx, "2025-12-29")["items"] == []  # antes del inicio (lunes)
    assert _agenda(client, ctx, "2026-02-02")["items"] == []  # después del término (lunes)


def test_inactive_medication_leaves_agenda_but_its_records_stay(client, ctx):
    med_id = _med(client, ctx).json()["id"]
    _dose(client, ctx, med_id, status="given", scheduledAt=AT_08, actualAt="2026-01-15T11:05:00Z")

    client.patch(f"/v1/patients/{ctx['pid']}/medications/{med_id}", json={"active": False}, headers=ctx["owner"])

    items = _agenda(client, ctx)["items"]
    assert [(i["localTime"], i["status"]) for i in items] == [("08:00", "given")]  # la de 20:00 ya no aparece
    assert client.get(f"/v1/patients/{ctx['pid']}/medications", headers=ctx["owner"]).json() == []
    assert len(client.get(f"/v1/patients/{ctx['pid']}/medications?includeInactive=true", headers=ctx["owner"]).json()) == 1
    assert _dose(client, ctx, med_id, status="given", scheduledAt=AT_20).json()["error"]["code"] == "medication_inactive"


def test_patient_time_zone_changes_the_utc_instant(client, ctx):
    client.patch(f"/v1/patients/{ctx['pid']}", json={"timeZone": "Pacific/Easter"}, headers=ctx["owner"])
    _med(client, ctx, schedule={"times": ["08:00"]})

    item = _agenda(client, ctx)["items"][0]

    assert item["localTime"] == "08:00"
    assert item["scheduledAt"] == "2026-01-15T13:00:00Z"  # Isla de Pascua en verano: UTC-5


def test_dst_gap_dose_is_listed_once_at_shifted_time(client, ctx):
    _med(client, ctx, schedule={"times": ["00:30", "01:30"]})

    items = _agenda(client, ctx, "2026-09-06")["items"]

    assert [(i["localTime"], i["scheduledAt"]) for i in items] == [("00:30", "2026-09-06T04:30:00Z")]


@pytest.mark.parametrize("payload", [{"timeZone": "Marte/Base"}, {"timeZone": None}])
def test_invalid_patient_time_zone(client, ctx, payload):
    assert client.patch(f"/v1/patients/{ctx['pid']}", json=payload, headers=ctx["owner"]).status_code == 422


# ---------- Registro de tomas ----------


def test_caregiver_records_dose_and_agenda_reflects_it(client, ctx):
    med_id = _med(client, ctx).json()["id"]

    response = _dose(client, ctx, med_id, status="given", scheduledAt=AT_08, actualAt="2026-01-15T11:10:00Z")

    log = response.json()
    assert response.status_code == 201
    assert log["recordedBy"] == ctx["carer_uid"]
    assert log["medicationName"] == "Paracetamol" and log["dose"] == "1 comprimido de 500 mg"
    statuses = [(i["localTime"], i["status"]) for i in _agenda(client, ctx)["items"]]
    assert statuses == [("08:00", "given"), ("20:00", "pending")]


def test_same_dose_cannot_be_recorded_twice(client, ctx):
    med_id = _med(client, ctx).json()["id"]
    _dose(client, ctx, med_id, status="given", scheduledAt=AT_08, actualAt="2026-01-15T11:05:00Z")

    again = _dose(client, ctx, med_id, headers=ctx["owner"], status="given", scheduledAt=AT_08, actualAt="2026-01-15T11:06:00Z")

    assert again.status_code == 409
    assert again.json()["error"]["code"] == "dose_already_recorded"


def test_simultaneous_records_of_same_dose_create_one(client, ctx):
    med_id = _med(client, ctx).json()["id"]
    from datetime import datetime

    body = DoseLogCreate(status="given", scheduled_at=datetime.fromisoformat(AT_08), actual_at=datetime.fromisoformat(AT_08))

    def attempt(uid):
        try:
            meds_service.log_dose(ctx["pid"], uid, med_id, body)
            return "ok"
        except AppError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(attempt, [ctx["owner_uid"], ctx["carer_uid"]] * 2))

    logs = get_db().collection(f"patients/{ctx['pid']}/medicationLogs").get()
    # Regla: como máximo un registro; cada intento termina en una respuesta controlada.
    assert results.count("ok") <= 1, results
    assert set(results) <= {"ok", "dose_already_recorded", "service_busy"}, results
    assert len(logs) == results.count("ok")


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ({"status": "given", "scheduledAt": "2026-01-15T12:00:00Z"}, "not_scheduled"),  # 09:00, no hay toma
        ({"status": "given", "scheduledAt": "2025-12-31T11:00:00Z"}, "not_scheduled"),  # antes del inicio
        ({"status": "given"}, "scheduled_at_required"),
        ({"status": "given", "scheduledAt": AT_08, "actualAt": "2999-01-01T00:00:00Z"}, "future_time"),
    ],
)
def test_dose_must_match_schedule_and_time(client, ctx, payload, code):
    med_id = _med(client, ctx).json()["id"]

    assert _dose(client, ctx, med_id, **payload).json()["error"]["code"] == code


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "delayed", "scheduledAt": AT_08, "actualAt": "2026-01-15T13:00:00Z"},  # sin motivo
        {"status": "delayed", "scheduledAt": AT_08, "reason": "Dormía"},  # sin hora real
        {"status": "omitted", "scheduledAt": AT_08},  # sin motivo
        {"status": "omitted", "scheduledAt": AT_08, "reason": "Vómito", "actualAt": "2026-01-15T11:00:00Z"},
        {"status": "given", "scheduledAt": "2026-01-15T11:00:00"},  # sin zona horaria
        {"status": "tomada", "scheduledAt": AT_08},
    ],
)
def test_dose_status_rules(client, ctx, payload):
    med_id = _med(client, ctx).json()["id"]

    assert _dose(client, ctx, med_id, **payload).status_code == 422


def test_delayed_and_omitted_with_reason(client, ctx):
    med_id = _med(client, ctx).json()["id"]

    delayed = _dose(client, ctx, med_id, status="delayed", scheduledAt=AT_08, actualAt="2026-01-15T13:00:00Z", reason="Dormía")
    omitted = _dose(client, ctx, med_id, status="omitted", scheduledAt=AT_20, reason="Se negó a tomarlo")

    assert delayed.json()["status"] == "delayed" and delayed.json()["reason"] == "Dormía"
    assert omitted.json()["actualAt"] is None
    assert [i["status"] for i in _agenda(client, ctx)["items"]] == ["delayed", "omitted"]


def test_caregiver_without_administer_permission_cannot_record(client, ctx):
    viewer_uid, viewer = register(client, "solo-mira@example.com")
    add_member(ctx["pid"], viewer_uid, "caregiver", ["patient.view"])
    med_id = _med(client, ctx).json()["id"]

    response = _dose(client, ctx, med_id, headers=viewer, status="given", scheduledAt=AT_08)

    assert response.json()["error"]["code"] == "forbidden"


def test_as_needed_medication(client, ctx):
    med_id = _med(client, ctx, name="Ibuprofeno", scheduleType="as_needed", schedule=None).json()["id"]

    first = _dose(client, ctx, med_id, status="given", actualAt="2026-01-15T15:00:00Z")
    second = _dose(client, ctx, med_id, status="given", actualAt="2026-01-15T21:00:00Z")
    with_schedule = _dose(client, ctx, med_id, status="given", scheduledAt=AT_08)
    omitted = _dose(client, ctx, med_id, status="omitted", reason="No hubo dolor")

    assert first.status_code == second.status_code == 201
    assert with_schedule.json()["error"]["code"] == "schedule_not_allowed"
    assert omitted.json()["error"]["code"] == "invalid_status"
    items = _agenda(client, ctx)["items"]
    assert [(i["name"], i["scheduledAt"], i["status"]) for i in items] == [("Ibuprofeno", None, "given")] * 2


def test_log_keeps_what_was_given_after_medication_changes(client, ctx):
    med_id = _med(client, ctx).json()["id"]
    _dose(client, ctx, med_id, status="given", scheduledAt=AT_08, actualAt="2026-01-15T11:05:00Z")

    client.patch(
        f"/v1/patients/{ctx['pid']}/medications/{med_id}",
        json={"dose": "2 comprimidos", "schedule": {"times": ["09:00"]}},
        headers=ctx["owner"],
    )

    items = _agenda(client, ctx)["items"]
    # La toma registrada a las 08:00 sigue visible con la dosis que se dio; la nueva de 09:00 queda pendiente.
    assert [(i["localTime"], i["status"], i["dose"]) for i in items] == [
        ("08:00", "given", "1 comprimido de 500 mg"),
        ("09:00", "pending", "2 comprimidos"),
    ]


# ---------- Correcciones ----------


def test_author_corrects_dose_and_previous_value_is_kept(client, ctx):
    med_id = _med(client, ctx).json()["id"]
    log_id = _dose(client, ctx, med_id, status="given", scheduledAt=AT_08, actualAt="2026-01-15T11:05:00Z").json()["id"]

    response = client.patch(
        f"/v1/patients/{ctx['pid']}/doses/{log_id}", json={"status": "omitted", "reason": "Me equivoqué de paciente"}, headers=ctx["carer"]
    )

    stored = get_db().document(f"patients/{ctx['pid']}/medicationLogs/{log_id}").get().to_dict()
    assert response.json()["status"] == "omitted" and response.json()["corrections"] == 1
    assert stored["history"][0]["status"] == "given"
    assert stored["history"][0]["replacedBy"] == ctx["carer_uid"]
    actions = [d.get("action") for d in get_db().collection("auditLogs").where(filter=FieldFilter("action", "==", "medication.dose_corrected")).stream()]
    assert actions == ["medication.dose_corrected"]


def test_only_author_or_owner_can_correct(client, ctx):
    other_uid, other = register(client, "otra-cuidadora@example.com")
    add_member(ctx["pid"], other_uid, "caregiver")
    med_id = _med(client, ctx).json()["id"]
    log_id = _dose(client, ctx, med_id, status="given", scheduledAt=AT_08, actualAt="2026-01-15T11:05:00Z").json()["id"]
    url = f"/v1/patients/{ctx['pid']}/doses/{log_id}"

    by_other = client.patch(url, json={"status": "omitted", "reason": "x"}, headers=other)
    by_owner = client.patch(url, json={"status": "delayed", "actualAt": "2026-01-15T12:00:00Z", "reason": "Llegó tarde"}, headers=ctx["owner"])

    assert by_other.json()["error"]["code"] == "forbidden"
    assert by_owner.status_code == 200 and by_owner.json()["status"] == "delayed"


# ---------- Historial de actividad (escritura) ----------


def test_actions_leave_activity_entries(client, ctx):
    med_id = _med(client, ctx).json()["id"]
    _dose(client, ctx, med_id, status="given", scheduledAt=AT_08, actualAt="2026-01-15T11:05:00Z")
    _dose(client, ctx, med_id, status="omitted", scheduledAt=AT_20, reason="Dormía")

    types = sorted(d.get("type") for d in get_db().collection(f"patients/{ctx['pid']}/activity").stream())

    assert types == ["medication.created", "medication.given", "medication.omitted"]
