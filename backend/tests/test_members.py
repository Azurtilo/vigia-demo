"""Invitaciones y miembros: flujo normal y, sobre todo, intentos de abuso."""

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.core.permissions import DEFAULT_PERMISSIONS
from app.services import memberships as memberships_service
from tests.helpers import register

pytestmark = pytest.mark.usefixtures("seeded_plans")

CODE_FORMAT = re.compile(r"^[A-HJKMNP-Z2-9]{4}(-[A-HJKMNP-Z2-9]{4}){4}$")


@pytest.fixture
def family(client):
    """Dueña con un paciente, y una cuidadora registrada (aún sin acceso)."""
    owner_uid, owner = register(client, "duena@example.com", "Dueña")
    carer_uid, carer = register(client, "cuidadora@example.com", "Cuidadora")
    patient_id = client.post("/v1/patients", json={"displayName": "Abuela Rosa"}, headers=owner).json()["id"]
    return {"owner": owner, "owner_uid": owner_uid, "carer": carer, "carer_uid": carer_uid, "pid": patient_id}


def _invite(client, f, email="cuidadora@example.com", relation="caregiver", **extra):
    return client.post(
        f"/v1/patients/{f['pid']}/invitations", json={"email": email, "relation": relation, **extra}, headers=f["owner"]
    )


def _accept(client, headers, code):
    return client.post("/v1/invitations/accept", json={"code": code}, headers=headers)


def _invitation_doc(invitation_id):
    return get_db().collection("invitations").document(invitation_id).get().to_dict()


# ---------- Crear invitación ----------


def test_invitation_code_is_shown_once_and_only_its_hash_is_stored(client, family):
    response = _invite(client, family)

    body = response.json()
    stored = _invitation_doc(body["invitation"]["id"])
    assert response.status_code == 201
    assert CODE_FORMAT.match(body["code"])
    assert body["invitation"]["status"] == "pending"
    assert body["invitation"]["permissions"] == list(DEFAULT_PERMISSIONS["caregiver"])
    assert body["code"] not in str(stored)
    assert body["code"].replace("-", "") not in str(stored)
    listed = client.get(f"/v1/patients/{family['pid']}/invitations", headers=family["owner"]).json()
    assert "code" not in listed[0]


def test_invitation_expires_in_seven_days(client, family):
    expires = datetime.fromisoformat(_invite(client, family).json()["invitation"]["expiresAt"])

    assert timedelta(days=6, hours=23) < expires - datetime.now(UTC) <= timedelta(days=7)


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "no-es-correo", "relation": "caregiver"},
        {"email": "x@example.com", "relation": "owner"},  # nadie puede ser invitado como dueño
        {"email": "x@example.com", "relation": "caregiver", "permissions": ["meds.administer"]},  # sin patient.view
        {"email": "x@example.com", "relation": "caregiver", "permissions": ["patient.view", "superpoder"]},
    ],
)
def test_invalid_invitations_are_rejected(client, family, payload):
    response = client.post(f"/v1/patients/{family['pid']}/invitations", json=payload, headers=family["owner"])

    assert response.status_code == 422


def test_owner_cannot_invite_self(client, family):
    response = _invite(client, family, email="DUENA@example.com")

    assert response.json()["error"]["code"] == "cannot_invite_self"


def test_only_owner_manages_invitations(client, family):
    code = _invite(client, family).json()["code"]
    _accept(client, family["carer"], code)
    _, stranger = register(client, "extrana@example.com")

    by_carer = client.post(
        f"/v1/patients/{family['pid']}/invitations",
        json={"email": "amiga@example.com", "relation": "family"},
        headers=family["carer"],
    )
    by_stranger = client.get(f"/v1/patients/{family['pid']}/invitations", headers=stranger)

    assert by_carer.json()["error"]["code"] == "owner_only"
    assert by_stranger.status_code == 404


def test_pending_invitations_are_capped(client, family):
    for i in range(memberships_service.MAX_PENDING_PER_PATIENT):
        assert _invite(client, family, email=f"p{i}@example.com").status_code == 201

    response = _invite(client, family, email="una-mas@example.com")

    assert response.json()["error"]["code"] == "too_many_invitations"


# ---------- Aceptar ----------


def test_accept_grants_access_with_invited_permissions(client, family):
    code = _invite(client, family).json()["code"]

    response = _accept(client, family["carer"], code)

    assert response.status_code == 200
    assert response.json()["id"] == family["pid"]
    assert response.json()["myRelation"] == "caregiver"
    assert response.json()["myPermissions"] == list(DEFAULT_PERMISSIONS["caregiver"])
    assert [p["id"] for p in client.get("/v1/patients", headers=family["carer"]).json()] == [family["pid"]]
    actions = [
        d.get("action")
        for d in get_db().collection("auditLogs").where(filter=FieldFilter("target", "==", f"patients/{family['pid']}")).stream()
    ]
    assert "invitation.created" in actions and "membership.joined" in actions


def test_custom_permissions_are_applied(client, family):
    code = _invite(client, family, permissions=["patient.view", "patient.edit"]).json()["code"]

    _accept(client, family["carer"], code)
    edit = client.patch(f"/v1/patients/{family['pid']}", json={"notes": "Duerme siesta"}, headers=family["carer"])

    assert edit.status_code == 200


def test_code_is_accepted_lowercase_and_without_dashes(client, family):
    code = _invite(client, family).json()["code"]

    response = _accept(client, family["carer"], code.replace("-", " ").lower())

    assert response.status_code == 200


def test_unknown_code_is_rejected(client, family):
    response = _accept(client, family["carer"], "AAAA-BBBB-CCCC-DDDD-EEEE")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "invitation_invalid"


def test_stolen_code_does_not_work_for_another_email(client, family):
    code = _invite(client, family).json()["code"]
    thief_uid, thief = register(client, "ladron@example.com")

    response = _accept(client, thief, code)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "invitation_email_mismatch"
    assert "cuidadora" not in response.text  # no revela el correo invitado
    assert client.get(f"/v1/patients/{family['pid']}", headers=thief).status_code == 404
    # La invitación sigue disponible para la persona correcta.
    assert _accept(client, family["carer"], code).status_code == 200


def test_code_cannot_be_reused(client, family):
    code = _invite(client, family).json()["code"]
    _accept(client, family["carer"], code)

    response = _accept(client, family["carer"], code)

    assert response.json()["error"]["code"] == "invitation_used"


def test_expired_code_is_rejected(client, family):
    created = _invite(client, family).json()
    get_db().collection("invitations").document(created["invitation"]["id"]).update(
        {"expiresAt": datetime.now(UTC) - timedelta(minutes=1)}
    )

    response = _accept(client, family["carer"], created["code"])
    listed = client.get(f"/v1/patients/{family['pid']}/invitations", headers=family["owner"]).json()

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "invitation_expired"
    assert listed[0]["status"] == "expired"


def test_revoked_code_is_rejected(client, family):
    created = _invite(client, family).json()
    inv_id = created["invitation"]["id"]

    revoke = client.delete(f"/v1/patients/{family['pid']}/invitations/{inv_id}", headers=family["owner"])
    again = client.delete(f"/v1/patients/{family['pid']}/invitations/{inv_id}", headers=family["owner"])
    response = _accept(client, family["carer"], created["code"])

    assert revoke.status_code == 200 and revoke.json()["status"] == "revoked"
    assert again.json()["error"]["code"] == "invitation_not_pending"
    assert response.json()["error"]["code"] == "invitation_revoked"


def test_revoke_requires_matching_patient(client, family):
    """No se puede anular una invitación de otro paciente usando la URL de un paciente propio."""
    inv_id = _invite(client, family).json()["invitation"]["id"]
    _, other_owner = register(client, "otra-duena@example.com")
    other_pid = client.post("/v1/patients", json={"displayName": "Otro"}, headers=other_owner).json()["id"]

    response = client.delete(f"/v1/patients/{other_pid}/invitations/{inv_id}", headers=other_owner)

    assert response.status_code == 404
    assert _invitation_doc(inv_id)["status"] == "pending"


def test_existing_member_cannot_accept_again(client, family):
    _accept(client, family["carer"], _invite(client, family).json()["code"])
    second = _invite(client, family, relation="family").json()["code"]

    response = _accept(client, family["carer"], second)

    assert response.json()["error"]["code"] == "already_member"


def test_cannot_join_archived_patient(client, family):
    code = _invite(client, family).json()["code"]
    client.post(f"/v1/patients/{family['pid']}/archive", headers=family["owner"])

    invite_now = _invite(client, family, email="otra@example.com")
    accept = _accept(client, family["carer"], code)

    assert invite_now.json()["error"]["code"] == "patient_archived"
    assert accept.json()["error"]["code"] == "patient_archived"


def test_simultaneous_accepts_create_one_membership(client, family):
    code = _invite(client, family).json()["code"]

    def attempt(_):
        try:
            memberships_service.accept_invitation(family["carer_uid"], "cuidadora@example.com", False, False, code)
            return "ok"
        except AppError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(attempt, range(4)))

    members = get_db().collection("memberships").where(filter=FieldFilter("patientId", "==", family["pid"])).get()
    assert results.count("ok") <= 1, results
    assert set(results) <= {"ok", "invitation_used", "already_member", "service_busy"}, results
    assert len(members) == 1 + results.count("ok")


def test_production_requires_verified_email(client, family):
    code = _invite(client, family).json()["code"]

    with pytest.raises(AppError) as exc:
        memberships_service.accept_invitation(family["carer_uid"], "cuidadora@example.com", False, True, code)

    assert exc.value.code == "email_not_verified"
    assert memberships_service.accept_invitation(family["carer_uid"], "cuidadora@example.com", True, True, code)


# ---------- Miembros ----------


def test_members_list_shows_names_and_permissions_without_emails(client, family):
    _accept(client, family["carer"], _invite(client, family).json()["code"])

    response = client.get(f"/v1/patients/{family['pid']}/members", headers=family["carer"])

    members = response.json()
    assert [(m["displayName"], m["relation"]) for m in members] == [("Dueña", "owner"), ("Cuidadora", "caregiver")]
    assert "@" not in response.text


def test_owner_changes_member_permissions_and_it_takes_effect(client, family):
    _accept(client, family["carer"], _invite(client, family).json()["code"])
    url = f"/v1/patients/{family['pid']}/members/{family['carer_uid']}"
    new = ["patient.view", "patient.edit", "meds.administer"]

    response = client.patch(url, json={"permissions": new}, headers=family["owner"])
    edit = client.patch(f"/v1/patients/{family['pid']}", json={"notes": "ok"}, headers=family["carer"])

    assert response.json()["permissions"] == sorted(new)
    assert edit.status_code == 200
    log = next(
        d.to_dict()
        for d in get_db()
        .collection("auditLogs")
        .where(filter=FieldFilter("action", "==", "membership.permissions_changed"))
        .stream()
    )
    assert log["details"]["from"] == sorted(DEFAULT_PERMISSIONS["caregiver"])
    assert log["details"]["to"] == sorted(new)


def test_member_cannot_escalate_own_permissions(client, family):
    _accept(client, family["carer"], _invite(client, family).json()["code"])
    url = f"/v1/patients/{family['pid']}/members/{family['carer_uid']}"

    response = client.patch(url, json={"permissions": ["patient.view", "patient.edit"]}, headers=family["carer"])

    assert response.json()["error"]["code"] == "owner_only"
    assert client.patch(f"/v1/patients/{family['pid']}", json={"notes": "x"}, headers=family["carer"]).status_code == 403


def test_owner_permissions_cannot_be_changed(client, family):
    url = f"/v1/patients/{family['pid']}/members/{family['owner_uid']}"

    response = client.patch(url, json={"permissions": ["patient.view"]}, headers=family["owner"])

    assert response.json()["error"]["code"] == "owner_permissions_fixed"


def test_permissions_update_requires_patient_view(client, family):
    _accept(client, family["carer"], _invite(client, family).json()["code"])
    url = f"/v1/patients/{family['pid']}/members/{family['carer_uid']}"

    response = client.patch(url, json={"permissions": ["meds.administer"]}, headers=family["owner"])

    assert response.status_code == 422


def test_owner_removes_member_and_access_ends(client, family):
    _accept(client, family["carer"], _invite(client, family).json()["code"])

    response = client.delete(f"/v1/patients/{family['pid']}/members/{family['carer_uid']}", headers=family["owner"])

    assert response.status_code == 204
    assert client.get(f"/v1/patients/{family['pid']}", headers=family["carer"]).status_code == 404
    assert client.get("/v1/patients", headers=family["carer"]).json() == []


def test_member_can_leave_but_owner_cannot(client, family):
    _accept(client, family["carer"], _invite(client, family).json()["code"])

    leave = client.delete(f"/v1/patients/{family['pid']}/members/{family['carer_uid']}", headers=family["carer"])
    owner_leave = client.delete(f"/v1/patients/{family['pid']}/members/{family['owner_uid']}", headers=family["owner"])

    assert leave.status_code == 204
    assert owner_leave.json()["error"]["code"] == "owner_cannot_leave"


def test_member_cannot_remove_others(client, family):
    _accept(client, family["carer"], _invite(client, family).json()["code"])
    second_uid, second = register(client, "hijo@example.com", "Hijo")
    _accept(client, second, _invite(client, family, email="hijo@example.com", relation="family").json()["code"])

    response = client.delete(f"/v1/patients/{family['pid']}/members/{second_uid}", headers=family["carer"])

    assert response.json()["error"]["code"] == "owner_only"
    assert len(client.get(f"/v1/patients/{family['pid']}/members", headers=family["owner"]).json()) == 3
