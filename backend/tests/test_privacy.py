"""Política de privacidad y consentimiento del paciente (spec 014, RF-019-07)."""

import pytest

from app.core.config import get_settings
from app.core.firebase import get_db
from app.services import edge_cache
from tests.helpers import add_member, register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")

MED = {"name": "Paracetamol", "dose": "1 comprimido", "scheduleType": "fixed", "schedule": {"times": ["08:00"]}, "startDate": "2026-01-01"}


@pytest.fixture
def enforced(monkeypatch):
    monkeypatch.setattr(get_settings(), "privacy_enforced", True)
    edge_cache.forget(everything=True)
    yield
    edge_cache.forget(everything=True)


@pytest.fixture
def ctx(client, enforced):
    owner_uid, owner = register(client, "duena@example.com", "Dueña")
    carer_uid, carer = register(client, "cuidadora@example.com", "Cuidadora")
    for headers in (owner, carer):
        assert client.post("/v1/privacy/accept", headers=headers).json()["accepted"] is True
    pid = client.post("/v1/patients", json={"displayName": "Abuela"}, headers=owner).json()["id"]
    add_member(pid, carer_uid, "caregiver")
    return {"owner": owner, "owner_uid": owner_uid, "carer": carer, "pid": pid}


def _consent(client, ctx, scope="cuidado", headers=None, **body):
    payload = {"scope": scope, "basis": "titular"} | body
    return client.post(f"/v1/patients/{ctx['pid']}/consents", json=payload, headers=headers or ctx["owner"])


def _code(response):
    return response.json()["error"]["code"]


# ---------- Política de la cuenta ----------


def test_the_api_requires_the_current_policy_but_me_and_privacy_stay_open(client, enforced):
    _, headers = register(client, "nueva@example.com")

    blocked = client.post("/v1/patients", json={"displayName": "X"}, headers=headers)
    me = client.get("/v1/me", headers=headers)
    status_ = client.get("/v1/privacy", headers=headers).json()

    assert blocked.status_code == 403 and _code(blocked) == "policy_not_accepted"
    assert me.status_code == 200 and me.json()["policyAcceptedVersion"] is None
    assert status_ == {"policyVersion": "2026-10-25", "accepted": False, "acceptedVersion": None, "enforced": True}

    assert client.post("/v1/privacy/accept", headers=headers).json()["accepted"] is True
    assert client.post("/v1/privacy/accept", headers=headers).json()["accepted"] is True  # repetir no cambia nada
    assert client.post("/v1/patients", json={"displayName": "X"}, headers=headers).status_code == 201


def test_a_new_policy_version_must_be_accepted_again(client, ctx, monkeypatch):
    monkeypatch.setattr(get_settings(), "privacy_policy_version", "2099-01-01")

    response = client.get(f"/v1/patients/{ctx['pid']}", headers=ctx["owner"])

    assert response.status_code == 403 and _code(response) == "policy_not_accepted"
    accepted = get_db().collection("users").document(ctx["owner_uid"]).collection("policyAcceptances").stream()
    assert [a.id for a in accepted] == ["2026-10-25"]


# ---------- Consentimiento del paciente ----------


def test_the_owner_records_consent_once_per_scope(client, ctx):
    first = _consent(client, ctx)
    again = _consent(client, ctx)
    by_representative = _consent(client, ctx, "deteccion", basis="representante", representativeName="Ana", representativeRelation="Hija")

    assert first.status_code == 201 and first.json()["policyVersion"] == "2026-10-25"
    assert again.status_code == 409 and _code(again) == "consent_already_active"
    assert by_representative.json()["representativeName"] == "Ana"
    listed = client.get(f"/v1/patients/{ctx['pid']}/consents", headers=ctx["carer"]).json()["items"]
    assert [(c["scope"], c["active"]) for c in listed] == [("cuidado", True), ("deteccion", True)]


@pytest.mark.parametrize(
    "body",
    [
        {"basis": "representante"},
        {"basis": "representante", "representativeName": "Ana"},
        {"basis": "titular", "representativeName": "Ana"},
        {"basis": "otro"},
    ],
)
def test_invalid_consent_bodies_are_rejected(client, ctx, body):
    assert _consent(client, ctx, **body).status_code == 422


def test_only_the_owner_records_or_revokes(client, ctx):
    assert _code(_consent(client, ctx, headers=ctx["carer"])) == "owner_only"
    _consent(client, ctx)
    revoked = client.post(f"/v1/patients/{ctx['pid']}/consents/cuidado/revoke", headers=ctx["carer"])
    assert revoked.status_code == 403


def test_without_care_consent_the_file_is_readable_but_no_new_data(client, ctx):
    url = f"/v1/patients/{ctx['pid']}"

    blocked = client.post(f"{url}/medications", json=MED, headers=ctx["owner"])
    assert blocked.status_code == 403 and _code(blocked) == "consent_required"
    assert client.get(url, headers=ctx["carer"]).status_code == 200
    assert client.get(f"{url}/agenda", headers=ctx["carer"]).status_code == 200

    _consent(client, ctx)
    med_id = client.post(f"{url}/medications", json=MED, headers=ctx["owner"]).json()["id"]
    client.post(f"{url}/consents/cuidado/revoke", headers=ctx["owner"])

    dose = client.post(f"{url}/medications/{med_id}/doses", json={"status": "given", "scheduledAt": "2026-01-15T11:00:00Z"}, headers=ctx["carer"])
    assert dose.status_code == 403 and _code(dose) == "consent_required"


def test_revoking_detection_consent_stops_the_node_at_once(client, ctx):
    set_plan(ctx["owner_uid"], "premium")
    _consent(client, ctx, "deteccion")
    node = client.post(f"/v1/patients/{ctx['pid']}/nodes", json={"name": "Dormitorio"}, headers=ctx["owner"]).json()
    auth = {"Authorization": f"Bearer {node['credential']}"}
    assert client.get("/api/v1/edge/status", headers=auth).status_code == 200

    client.post(f"/v1/patients/{ctx['pid']}/consents/deteccion/revoke", headers=ctx["owner"])

    assert client.get("/api/v1/edge/status", headers=auth).status_code == 403


def test_every_record_is_kept_with_its_revocation(client, ctx):
    _consent(client, ctx)
    revoked = client.post(f"/v1/patients/{ctx['pid']}/consents/cuidado/revoke", headers=ctx["owner"])
    again = client.post(f"/v1/patients/{ctx['pid']}/consents/cuidado/revoke", headers=ctx["owner"])
    _consent(client, ctx, basis="representante", representativeName="Ana", representativeRelation="Hija")

    assert revoked.json()["active"] is False and revoked.json()["revokedAt"] is not None
    assert again.status_code == 409
    records = [r.to_dict() for r in get_db().collection("patients").document(ctx["pid"]).collection("consentRecords").stream()]
    assert sorted((r["basis"], r["active"]) for r in records) == [("representante", True), ("titular", False)]
