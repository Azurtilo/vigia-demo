"""Exportación, eliminación y purga por plazos (spec 014, RF-019-24..27, D-064, D-065, D-098)."""

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from firebase_admin import auth

from app.core.firebase import get_db
from app.services import edge_cache, retention
from tests.helpers import add_member, bearer, make_token, register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")

MED = {"name": "Paracetamol", "dose": "1 comprimido", "scheduleType": "fixed", "schedule": {"times": ["08:00"]}, "startDate": "2026-01-01"}
AT_08 = "2026-01-15T11:00:00Z"


@pytest.fixture(autouse=True)
def _clean_cache():
    edge_cache.forget(everything=True)
    yield
    edge_cache.forget(everything=True)


@pytest.fixture
def ctx(client):
    owner_uid, owner = register(client, "duena@example.com", "Dueña")
    carer_uid, carer = register(client, "cuidadora@example.com", "Cuidadora")
    set_plan(owner_uid, "premium")
    pid = client.post("/v1/patients", json={"displayName": "Abuela Rosa"}, headers=owner).json()["id"]
    add_member(pid, carer_uid, "caregiver")
    db = get_db()
    db.collection("patients").document(pid).collection("consents").document("deteccion").set({"active": True})
    med_id = client.post(f"/v1/patients/{pid}/medications", json=MED, headers=owner).json()["id"]
    client.post(f"/v1/patients/{pid}/medications/{med_id}/doses", json={"status": "given", "scheduledAt": AT_08}, headers=carer)
    node = client.post(f"/v1/patients/{pid}/nodes", json={"name": "Dormitorio"}, headers=owner).json()
    invitation = client.post(f"/v1/patients/{pid}/invitations", json={"email": "hijo@example.com", "relation": "family"}, headers=owner).json()
    device = {"installationId": str(uuid.uuid4()), "enabled": True, "token": "token-secreto-del-telefono-xxxxxxxx", "platform": "android"}
    client.post("/v1/devices", json=device, headers=carer)
    return {
        "owner": owner, "owner_uid": owner_uid, "carer": carer, "carer_uid": carer_uid, "pid": pid,
        "node": node, "invitation": invitation, "device": device,
    }


def _secrets(ctx) -> list[str]:
    return [ctx["node"]["credential"], ctx["invitation"]["code"], ctx["invitation"]["invitation"]["id"], ctx["device"]["token"]]


# ---------- Exportación ----------


def test_the_owner_exports_the_whole_patient_without_secrets(client, ctx):
    response = client.get(f"/v1/patients/{ctx['pid']}/export", headers=ctx["owner"])

    data = response.json()
    assert response.status_code == 200 and data["kind"] == "patient"
    assert data["patient"]["displayName"] == "Abuela Rosa"
    assert len(data["medications"]) == 1 and len(data["medicationLogs"]) == 1 and data["nodes"][0]["name"] == "Dormitorio"
    assert {m["relation"] for m in data["members"]} == {"owner", "caregiver"}
    text = json.dumps(data)
    assert not any(secret in text for secret in _secrets(ctx))
    assert "credentialHash" not in text and "payloadHash" not in text
    assert client.get(f"/v1/patients/{ctx['pid']}/export", headers=ctx["carer"]).status_code == 403


def test_the_caregiver_exports_what_she_did_not_the_patient_file(client, ctx):
    data = client.get("/v1/me/export", headers=ctx["carer"]).json()

    assert data["kind"] == "account" and data["account"]["displayName"] == "Cuidadora"
    assert [(r["collection"], r["status"]) for r in data["recordsInOtherPatients"]] == [("medicationLogs", "given")]
    assert data["devices"][0]["platform"] == "android"
    text = json.dumps(data)
    assert "Abuela Rosa" not in text  # no es la ficha del paciente ajeno
    assert not any(secret in text for secret in _secrets(ctx))


# ---------- Eliminar paciente ----------


def _deleted_everywhere(pid: str) -> bool:
    db = get_db()
    patient = db.collection("patients").document(pid)
    leftovers = [
        patient.get().exists,
        any(True for _ in patient.collection("medicationLogs").stream()),
        any(True for _ in patient.collection("medications").stream()),
        *(
            any(True for _ in db.collection(c).where("patientId", "==", pid).stream())
            for c in ("memberships", "edgeNodes", "invitations")
        ),
    ]
    return not any(leftovers)


def test_a_wrong_name_deletes_nothing(client, ctx):
    response = client.post(f"/v1/patients/{ctx['pid']}/delete", json={"confirmName": "Abuela"}, headers=ctx["owner"])

    assert response.status_code == 422 and response.json()["error"]["code"] == "name_mismatch"
    assert get_db().collection("patients").document(ctx["pid"]).get().exists


def test_deleting_a_patient_removes_every_trace_and_frees_the_slot(client, ctx):
    auth_header = {"Authorization": f"Bearer {ctx['node']['credential']}"}
    assert client.get("/api/v1/edge/status", headers=auth_header).status_code == 200

    response = client.post(f"/v1/patients/{ctx['pid']}/delete", json={"confirmName": "  abuela rosa "}, headers=ctx["owner"])

    assert response.json() == {"deleted": True} and _deleted_everywhere(ctx["pid"])
    assert get_db().collection("users").document(ctx["owner_uid"]).get().get("activePatientCount") == 0
    assert client.get(f"/v1/patients/{ctx['pid']}", headers=ctx["carer"]).status_code == 404
    assert client.get("/api/v1/edge/status", headers=auth_header).status_code == 401
    operations = [o.to_dict() for o in get_db().collection("privacyOperations").stream()]
    assert [o["kind"] for o in operations] == ["delete_patient"] and "Rosa" not in json.dumps(operations, default=str)


def test_only_the_owner_deletes_a_patient(client, ctx):
    response = client.post(f"/v1/patients/{ctx['pid']}/delete", json={"confirmName": "Abuela Rosa"}, headers=ctx["carer"])

    assert response.status_code == 403


# ---------- Eliminar cuenta ----------


def test_deleting_the_account_requires_a_recent_sign_in(client, ctx):
    stale = bearer(make_token(ctx["owner_uid"], email="duena@example.com", auth_age=10 * 60))

    response = client.delete("/v1/me", headers=stale)

    assert response.status_code == 401 and response.json()["error"]["code"] == "reauth_required"
    assert get_db().collection("patients").document(ctx["pid"]).get().exists


def test_the_owner_account_goes_with_its_patients(client, ctx):
    response = client.delete("/v1/me", headers=ctx["owner"])

    assert response.json() == {"deleted": True} and _deleted_everywhere(ctx["pid"])
    with pytest.raises(auth.UserNotFoundError):
        auth.get_user(ctx["owner_uid"])
    assert client.get("/v1/me", headers=ctx["owner"]).status_code == 401


def test_a_caregiver_account_leaves_an_anonymous_author_on_records_of_others(client, ctx):
    response = client.delete("/v1/me", headers=ctx["carer"])

    assert response.status_code == 200
    db = get_db()
    stub = db.collection("users").document(ctx["carer_uid"]).get().to_dict()
    assert stub["status"] == "deleted" and stub["email"] is None and stub["displayName"] == "Cuenta eliminada"
    logs = [l.to_dict() for l in db.collection("patients").document(ctx["pid"]).collection("medicationLogs").stream()]
    assert [l["recordedBy"] for l in logs] == [ctx["carer_uid"]]  # el registro queda, con autor anónimo
    assert not db.collection("memberships").document(f"{ctx['pid']}_{ctx['carer_uid']}").get().exists
    assert not any(True for _ in db.collection("devices").where("uid", "==", ctx["carer_uid"]).stream())
    members = client.get(f"/v1/patients/{ctx['pid']}/members", headers=ctx["owner"]).json()
    assert ctx["carer_uid"] not in [m["uid"] for m in members]


# ---------- Purga por plazos (D-064) ----------


def test_the_daily_purge_follows_the_retention_periods(client, ctx):
    db = get_db()
    now = datetime.now(UTC)
    observations = db.collection("patients").document(ctx["pid"]).collection("observations")
    rows = {
        "comun-31": ("", 31), "comun-29": ("", 29), "riesgo-31": ("fall", 31), "riesgo-400": ("fall", 400),
    }
    for doc_id, (risk, days) in rows.items():
        observations.document(doc_id).set({"risk": risk, "observedAt": now - timedelta(days=days)})
    alerts = db.collection("patients").document(ctx["pid"]).collection("alerts")
    alerts.document("vieja").set({"kind": "fall", "occurredAt": now - timedelta(days=400)})
    alerts.document("reciente").set({"kind": "fall", "occurredAt": now - timedelta(days=10)})
    db.collection("reminderDeliveries").document("viejo").set({"patientId": ctx["pid"], "sentAt": now - timedelta(days=31)})
    invitation_id = ctx["invitation"]["invitation"]["id"]
    db.collection("invitations").document(invitation_id).update({"expiresAt": now - timedelta(days=91)})
    archived = client.post("/v1/patients", json={"displayName": "Tío"}, headers=ctx["owner"]).json()["id"]
    client.post(f"/v1/patients/{archived}/archive", headers=ctx["owner"])
    db.collection("patients").document(archived).update({"archivedAt": now - timedelta(days=731)})

    counts = retention.purge(now)

    assert sorted(o.id for o in observations.stream()) == ["comun-29", "riesgo-31"]
    assert [a.id for a in alerts.stream()] == ["reciente"]
    assert counts["observations_without_risk"] == 1 and counts["observations_with_risk"] == 1
    assert counts["closed_invitations"] == 1 and counts["reminder_receipts"] == 1 and counts["archived_patients"] == 1
    assert not db.collection("patients").document(archived).get().exists
    assert db.collection("patients").document(ctx["pid"]).collection("medicationLogs").limit(1).get()  # paciente activo: se conserva


def test_a_recently_archived_patient_is_kept(client, ctx):
    client.post(f"/v1/patients/{ctx['pid']}/archive", headers=ctx["owner"])

    assert retention.purge()["archived_patients"] == 0
    assert get_db().collection("patients").document(ctx["pid"]).get().exists


def test_the_purge_runs_once_per_day(monkeypatch, client):
    monkeypatch.setattr(retention, "_last_day", None)
    calls = []
    monkeypatch.setattr(retention, "purge", lambda now=None: calls.append(now) or {})
    day = datetime(2026, 11, 1, 3, 0, tzinfo=UTC)

    retention.run_daily(day)
    retention.run_daily(day + timedelta(hours=5))
    retention.run_daily(day + timedelta(days=1))

    assert len(calls) == 2
