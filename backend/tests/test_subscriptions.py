"""Cambios de plan simulados: preview, confirmación al bajar, registro y concurrencia con altas."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.errors import AppError
from app.core.firebase import get_db
from app.models.patient import PatientCreate
from app.services import patients as patients_service
from app.services import subscriptions as subscriptions_service
from tests.helpers import register, set_plan

pytestmark = pytest.mark.usefixtures("seeded_plans")


def _change(client, headers, plan_id, **extra):
    return client.post("/v1/me/subscription/change", json={"planId": plan_id, **extra}, headers=headers)


def _patients(client, headers, n):
    for i in range(n):
        assert client.post("/v1/patients", json={"displayName": f"P{i}"}, headers=headers).status_code == 201


def _changes(uid):
    return [d.to_dict() for d in get_db().collection("subscriptionChanges").where(filter=FieldFilter("uid", "==", uid)).stream()]


def test_plans_are_listed_in_order_with_test_prices(client):
    _, headers = register(client, "ve-planes@example.com")

    plans = client.get("/v1/plans", headers=headers).json()

    assert [(p["id"], p["priceClp"], p["maxPatients"]) for p in plans] == [
        ("free", 0, 1),
        ("plus", 4990, 3),
        ("premium", 9990, None),
    ]
    assert all(p["priceIsTest"] for p in plans)
    assert plans[2]["features"]["cameras"] is True


def test_new_account_subscription(client):
    _, headers = register(client, "nueva@example.com")

    sub = client.get("/v1/me/subscription", headers=headers).json()

    assert sub["planId"] == "free" and sub["simulated"] is True and sub["status"] == "active"
    assert sub["usage"]["activePatients"] == 0 and sub["recentChanges"] == []


def test_upgrade_is_immediate_and_recorded(client):
    uid, headers = register(client, "sube@example.com")

    response = _change(client, headers, "plus")

    sub = response.json()
    assert response.status_code == 200
    assert sub["planId"] == "plus" and sub["usage"]["maxPatients"] == 3
    assert sub["recentChanges"][0] | {"id": None, "at": None} == {
        "id": None, "at": None, "fromPlan": "free", "toPlan": "plus", "changedBy": uid, "actorRole": "user",
        "priceClp": 4990, "priceIsTest": True, "overLimitConfirmed": False,
    }
    _patients(client, headers, 3)  # el nuevo límite aplica de inmediato
    audit = [d.to_dict() for d in get_db().collection("auditLogs").where(filter=FieldFilter("action", "==", "subscription.changed")).stream()]
    assert audit[0]["details"]["from"] == "free" and audit[0]["details"]["to"] == "plus"


def test_same_plan_is_rejected(client):
    _, headers = register(client, "igual@example.com")

    assert _change(client, headers, "free").json()["error"]["code"] == "already_on_plan"


def test_preview_explains_downgrade_without_applying_it(client):
    uid, headers = register(client, "simula@example.com")
    set_plan(uid, "plus")
    _patients(client, headers, 3)

    preview = client.get("/v1/me/subscription/preview?planId=free", headers=headers).json()

    assert preview["overLimit"] is True and preview["requiresConfirmation"] is True
    assert preview["activePatients"] == 3 and preview["target"]["maxPatients"] == 1
    assert "registro de cambios de posición" in preview["lostFeatures"]
    assert "historial visible limitado a 30 días" in preview["lostFeatures"]
    assert "No se borrará nada" in preview["message"]
    # La simulación no cambia nada.
    assert client.get("/v1/me/subscription", headers=headers).json()["planId"] == "plus"
    assert _changes(uid) == []


def test_downgrade_over_limit_requires_confirmation(client):
    uid, headers = register(client, "baja@example.com")
    set_plan(uid, "plus")
    _patients(client, headers, 3)

    rejected = _change(client, headers, "free")
    confirmed = _change(client, headers, "free", confirmOverLimit=True)

    assert rejected.status_code == 409 and rejected.json()["error"]["code"] == "downgrade_over_limit"
    assert "3 pacientes activos" in rejected.json()["error"]["message"]
    assert confirmed.status_code == 200 and confirmed.json()["planId"] == "free"
    assert confirmed.json()["recentChanges"][0]["overLimitConfirmed"] is True
    assert len(client.get("/v1/patients", headers=headers).json()) == 3  # no se borra nada
    assert client.post("/v1/patients", json={"displayName": "Otro"}, headers=headers).status_code == 403


def test_downgrade_within_limit_needs_no_confirmation(client):
    uid, headers = register(client, "baja-ok@example.com")
    set_plan(uid, "plus")
    _patients(client, headers, 1)

    preview = client.get("/v1/me/subscription/preview?planId=free", headers=headers).json()
    response = _change(client, headers, "free")

    assert preview["requiresConfirmation"] is False and preview["lostFeatures"]
    assert response.status_code == 200


def test_unavailable_plan_cannot_be_chosen_but_is_kept_by_current_users(client):
    keeper_uid, keeper = register(client, "ya-tenia@example.com")
    _, newcomer = register(client, "recien@example.com")
    _change(client, keeper, "plus")
    get_db().collection("plans").document("plus").update({"available": False})

    listed = [p["id"] for p in client.get("/v1/plans", headers=newcomer).json()]
    response = _change(client, newcomer, "plus")

    assert listed == ["free", "premium"]
    assert response.json()["error"]["code"] == "plan_unavailable"
    assert client.get("/v1/me/subscription", headers=keeper).json()["planId"] == "plus"


def test_account_without_subscription_document_can_change(client):
    uid, headers = register(client, "antigua@example.com")
    get_db().collection("subscriptions").document(uid).delete()  # como las cuentas creadas antes de la Fase 3

    response = _change(client, headers, "premium")

    assert response.json()["planId"] == "premium"
    assert response.json()["recentChanges"][0]["fromPlan"] is None


def test_changes_are_listed_newest_first(client):
    _, headers = register(client, "varios@example.com")
    _change(client, headers, "plus")
    _change(client, headers, "premium")

    changes = client.get("/v1/me/subscription", headers=headers).json()["recentChanges"]

    assert [(c["fromPlan"], c["toPlan"]) for c in changes] == [("plus", "premium"), ("free", "plus")]


@pytest.mark.parametrize("body", [{"planId": "gold"}, {"planId": "plus", "price": 0}, {}])
def test_invalid_change_requests(client, body):
    _, headers = register(client, "invalida@example.com")

    assert client.post("/v1/me/subscription/change", json=body, headers=headers).status_code == 422


def test_downgrade_racing_with_patient_creation_never_breaks_the_limit(client):
    """Plus con 1 paciente: 3 altas simultáneas y una baja a Gratis SIN confirmación.

    Cualquiera sea el orden en que Firestore las serialice, si el plan termina en Gratis no
    puede haber más de 1 paciente activo (la baja sin confirmación solo procede con ≤ 1).
    """
    uid, headers = register(client, "carrera@example.com")
    set_plan(uid, "plus")
    _patients(client, headers, 1)

    def create(i):
        try:
            patients_service.create_patient(uid, PatientCreate(display_name=f"Simultáneo {i}"))
            return "created"
        except AppError as exc:
            return exc.code

    def downgrade(_):
        try:
            subscriptions_service.change_plan(uid, "free", False, uid, "user")
            return "downgraded"
        except AppError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(create, i) for i in range(3)] + [pool.submit(downgrade, 0)]
        results = [f.result() for f in futures]

    plan_id = client.get("/v1/me/subscription", headers=headers).json()["planId"]
    active = get_db().collection("users").document(uid).get().get("activePatientCount")
    owned = len(
        get_db().collection("patients").where(filter=FieldFilter("ownerUid", "==", uid))
        .where(filter=FieldFilter("status", "==", "active")).get()
    )
    assert active == owned, results
    assert set(results) <= {"created", "downgraded", "plan_limit_reached", "downgrade_over_limit", "service_busy"}, results
    if plan_id == "free":
        assert owned <= 1, results
    else:
        assert owned <= 3, results
