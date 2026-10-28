"""Pacientes: acceso, edición, archivo y límites de plan (incluidas solicitudes simultáneas)."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.permissions import ALL_PERMISSIONS, DEFAULT_PERMISSIONS
from app.core.firebase import get_db
from app.models.patient import PatientCreate
from app.services import patients as patients_service
from tests.helpers import register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")


def _create(client, headers, name="Abuela Rosa", **extra):
    return client.post("/v1/patients", json={"displayName": name, **extra}, headers=headers)


def _active_count(uid: str) -> int:
    return get_db().collection("users").document(uid).get().get("activePatientCount")


def _owned_active(uid: str) -> int:
    query = (
        get_db()
        .collection("patients")
        .where(filter=FieldFilter("ownerUid", "==", uid))
        .where(filter=FieldFilter("status", "==", "active"))
    )
    return len(list(query.stream()))


# ---------- Registro y suscripción ----------


def test_registration_starts_on_simulated_free_plan(client):
    uid, headers = register(client, "nueva@example.com")

    sub = get_db().collection("subscriptions").document(uid).get().to_dict()
    plan = client.get("/v1/me/plan", headers=headers).json()

    assert sub["planId"] == "free" and sub["simulated"] is True
    assert plan == {
        "planId": "free",
        "planName": "Gratis",
        "maxPatients": 1,
        "activePatients": 0,
        "canAddPatient": True,
    }


# ---------- Alta ----------


def test_create_patient_makes_caller_owner_with_all_permissions(client):
    uid, headers = register(client, "duena@example.com")

    response = _create(
        client,
        headers,
        birthDate="1940-05-17",
        allergies=["Penicilina"],
        emergencyContacts=[{"name": "Juan", "phone": "+56 9 1234 5678", "relation": "Hijo"}],
    )

    body = response.json()
    assert response.status_code == 201
    assert body["ownerUid"] == uid
    assert body["status"] == "active"
    assert body["birthDate"] == "1940-05-17"
    assert body["myRelation"] == "owner"
    assert body["myPermissions"] == list(ALL_PERMISSIONS)
    assert _active_count(uid) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"displayName": ""},
        {"displayName": "X", "ownerUid": "otra-persona"},  # no se puede elegir dueño
        {"displayName": "X", "status": "archived"},
        {"displayName": "X", "birthDate": "2999-01-01"},
        {"displayName": "X", "emergencyContacts": [{"name": "A", "phone": "llamar-al-vecino"}]},
        {"displayName": "X", "emergencyContacts": [{"name": f"C{i}", "phone": "+56911111111"} for i in range(4)]},
    ],
)
def test_create_patient_rejects_invalid_data(client, payload):
    uid, headers = register(client, "validaciones@example.com")

    response = client.post("/v1/patients", json=payload, headers=headers)

    assert response.status_code == 422
    assert _active_count(uid) == 0


# ---------- Límites de plan ----------


def test_free_plan_blocks_second_patient(client):
    uid, headers = register(client, "gratis@example.com")
    assert _create(client, headers).status_code == 201

    response = _create(client, headers, "Segundo")

    error = response.json()["error"]
    assert response.status_code == 403
    assert error["code"] == "plan_limit_reached"
    assert "Gratis" in error["message"] and "1 paciente" in error["message"]
    assert _active_count(uid) == _owned_active(uid) == 1
    assert client.get("/v1/me/plan", headers=headers).json()["canAddPatient"] is False


def test_plus_plan_allows_three_and_blocks_fourth(client):
    uid, headers = register(client, "plus@example.com")
    set_plan(uid, "plus")

    statuses = [_create(client, headers, f"P{i}").status_code for i in range(4)]

    assert statuses == [201, 201, 201, 403]
    assert _active_count(uid) == _owned_active(uid) == 3


def test_premium_plan_has_no_fixed_limit(client):
    uid, headers = register(client, "premium@example.com")
    set_plan(uid, "premium")

    statuses = [_create(client, headers, f"P{i}").status_code for i in range(6)]

    assert statuses == [201] * 6
    assert client.get("/v1/me/plan", headers=headers).json()["maxPatients"] is None


def test_missing_plans_configuration_is_rejected_not_guessed(client):
    uid, headers = register(client, "sin-planes@example.com")
    for plan in get_db().collection("plans").stream():
        plan.reference.delete()

    response = _create(client, headers)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "plans_not_configured"
    assert _active_count(uid) == 0


@pytest.mark.parametrize(("plan_id", "already"), [("free", 0), ("plus", 2)])
def test_simultaneous_creations_never_exceed_plan_limit(client, plan_id, already):
    uid, headers = register(client, f"carrera-{plan_id}@example.com")
    set_plan(uid, plan_id)
    for i in range(already):
        assert _create(client, headers, f"Previo {i}").status_code == 201

    def attempt(i: int) -> str:
        try:
            patients_service.create_patient(uid, PatientCreate(display_name=f"Simultáneo {i}"))
            return "ok"
        except AppError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(attempt, range(5)))

    assert results.count("ok") <= 1, results
    assert set(results) <= {"ok", "plan_limit_reached", "service_busy"}, results
    # El contador y los documentos reales siempre coinciden y nunca superan el límite.
    assert _active_count(uid) == _owned_active(uid) == already + results.count("ok")
    assert _owned_active(uid) <= {"free": 1, "plus": 3}[plan_id]


def test_downgrade_keeps_patients_but_blocks_new_ones(client):
    uid, headers = register(client, "baja-de-plan@example.com")
    set_plan(uid, "plus")
    ids = [_create(client, headers, f"P{i}").json()["id"] for i in range(3)]

    set_plan(uid, "free")

    assert len(client.get("/v1/patients", headers=headers).json()) == 3  # no se borra nada
    assert _create(client, headers, "Nuevo").json()["error"]["code"] == "plan_limit_reached"
    # Archivar sigue permitido; mientras siga excedido, no puede agregar ni reactivar.
    client.post(f"/v1/patients/{ids[0]}/archive", headers=headers)
    assert _create(client, headers, "Nuevo").status_code == 403
    assert client.post(f"/v1/patients/{ids[0]}/reactivate", headers=headers).status_code == 403
    client.post(f"/v1/patients/{ids[1]}/archive", headers=headers)
    assert _create(client, headers, "Nuevo").status_code == 403  # 1 activo = límite Gratis
    assert _active_count(uid) == _owned_active(uid) == 1


# ---------- Archivar y reactivar ----------


def test_archive_frees_a_slot_and_keeps_the_patient(client):
    uid, headers = register(client, "archiva@example.com")
    patient_id = _create(client, headers).json()["id"]

    archived = client.post(f"/v1/patients/{patient_id}/archive", headers=headers)
    second = _create(client, headers, "Otro")
    reactivate = client.post(f"/v1/patients/{patient_id}/reactivate", headers=headers)

    assert archived.status_code == 200 and archived.json()["status"] == "archived"
    assert second.status_code == 201
    assert reactivate.json()["error"]["code"] == "plan_limit_reached"
    assert client.get(f"/v1/patients/{patient_id}", headers=headers).status_code == 200
    assert _active_count(uid) == 1


def test_archive_and_reactivate_are_not_repeatable(client):
    _, headers = register(client, "repite@example.com")
    patient_id = _create(client, headers).json()["id"]

    assert client.post(f"/v1/patients/{patient_id}/reactivate", headers=headers).status_code == 409
    client.post(f"/v1/patients/{patient_id}/archive", headers=headers)
    assert client.post(f"/v1/patients/{patient_id}/archive", headers=headers).status_code == 409


def test_list_filters_by_status(client):
    uid, headers = register(client, "lista@example.com")
    set_plan(uid, "plus")
    a = _create(client, headers, "Beatriz").json()["id"]
    _create(client, headers, "alberto")
    client.post(f"/v1/patients/{a}/archive", headers=headers)

    def names(status):
        return [p["displayName"] for p in client.get(f"/v1/patients?status={status}", headers=headers).json()]

    assert names("active") == ["alberto"]
    assert names("archived") == ["Beatriz"]
    assert names("all") == ["alberto", "Beatriz"]


# ---------- Edición ----------


def test_patch_updates_only_sent_fields_and_audits_field_names(client):
    uid, headers = register(client, "edita@example.com")
    patient_id = _create(client, headers, notes="Nota inicial", mobility="Usa andador").json()["id"]

    response = client.patch(
        f"/v1/patients/{patient_id}", json={"careNeeds": "Cambio de pañal", "notes": None}, headers=headers
    )

    body = response.json()
    assert response.status_code == 200
    assert body["careNeeds"] == "Cambio de pañal"
    assert body["notes"] is None  # null borra el campo
    assert body["mobility"] == "Usa andador"  # no enviado = sin cambios
    log = next(
        d.to_dict()
        for d in get_db().collection("auditLogs").where(filter=FieldFilter("action", "==", "patient.updated")).stream()
    )
    assert log["details"] == {"fields": ["careNeeds", "notes"]}
    assert "Cambio de pañal" not in str(log)


def test_patch_cannot_clear_name(client):
    _, headers = register(client, "nombre@example.com")
    patient_id = _create(client, headers).json()["id"]

    response = client.patch(f"/v1/patients/{patient_id}", json={"displayName": None}, headers=headers)

    assert response.status_code == 422


def test_archived_patient_is_read_only(client):
    _, headers = register(client, "solo-lectura@example.com")
    patient_id = _create(client, headers).json()["id"]
    client.post(f"/v1/patients/{patient_id}/archive", headers=headers)

    response = client.patch(f"/v1/patients/{patient_id}", json={"notes": "x"}, headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "patient_archived"


# ---------- Acceso de otras personas ----------


def test_stranger_cannot_see_or_touch_patient(client):
    _, owner = register(client, "propia@example.com")
    _, stranger = register(client, "ajena@example.com")
    patient_id = _create(client, owner).json()["id"]

    calls = [
        client.get(f"/v1/patients/{patient_id}", headers=stranger),
        client.patch(f"/v1/patients/{patient_id}", json={"notes": "hackeo"}, headers=stranger),
        client.post(f"/v1/patients/{patient_id}/archive", headers=stranger),
    ]

    # 404 (no 403): un extraño no puede ni confirmar que el paciente existe.
    assert [c.status_code for c in calls] == [404, 404, 404]
    assert client.get("/v1/patients", headers=stranger).json() == []
    assert client.get(f"/v1/patients/{patient_id}", headers=owner).json()["notes"] is None


def test_nonexistent_patient_is_404(client):
    _, headers = register(client, "busca@example.com")

    assert client.get("/v1/patients/no-existe", headers=headers).status_code == 404


def test_caregiver_permissions_are_enforced(client):
    """Membresía de cuidador creada directamente (las invitaciones llegan en el paso 3.2)."""
    _, owner = register(client, "familia@example.com")
    carer_uid, carer = register(client, "cuidadora@example.com")
    patient_id = _create(client, owner).json()["id"]
    get_db().collection("memberships").document(f"{patient_id}_{carer_uid}").set(
        {
            "patientId": patient_id,
            "uid": carer_uid,
            "relation": "caregiver",
            "permissions": list(DEFAULT_PERMISSIONS["caregiver"]),
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
    )

    view = client.get(f"/v1/patients/{patient_id}", headers=carer)
    edit = client.patch(f"/v1/patients/{patient_id}", json={"notes": "x"}, headers=carer)
    archive = client.post(f"/v1/patients/{patient_id}/archive", headers=carer)

    assert view.status_code == 200 and view.json()["myRelation"] == "caregiver"
    assert "patient.edit" not in view.json()["myPermissions"]
    assert edit.json()["error"]["code"] == "forbidden"
    assert archive.json()["error"]["code"] == "owner_only"
    assert [p["id"] for p in client.get("/v1/patients", headers=carer).json()] == [patient_id]
    # El paciente ajeno no consume el plan de la cuidadora.
    assert client.get("/v1/me/plan", headers=carer).json()["activePatients"] == 0
