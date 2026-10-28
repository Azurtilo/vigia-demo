"""Prepara dueño, paciente Premium con consentimiento y nodo en el backend local (emuladores).

Uso (desde backend/, con .venv-backend y el backend local en marcha):
    python scripts/smoke_edge_setup.py http://127.0.0.1:8765
Imprime: <patient_id> <token_del_nodo> <encabezado del dueño>
"""

import os
import sys
import uuid

os.environ.setdefault("VIGIA_FIREBASE_PROJECT_ID", "demo-vigia-test")
os.environ.setdefault("VIGIA_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
os.environ.setdefault("VIGIA_FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
sys.path.insert(0, os.getcwd())

import requests  # noqa: E402
from firebase_admin import auth  # noqa: E402

from app.core.firebase import get_db, init_firebase  # noqa: E402
from app.services.plans import seed_plans, subscription_ref  # noqa: E402
from tests.helpers import make_token  # noqa: E402

server = sys.argv[1]
# Arma tokens sin firma: solo sirve (y solo se permite) con los emuladores.
assert os.environ["VIGIA_FIREBASE_PROJECT_ID"].startswith("demo-"), "Solo con proyectos demo-* de los emuladores"
init_firebase()
seed_plans()
email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
user = auth.create_user(email=email, password="clave-de-prueba")
owner = {"Authorization": f"Bearer {make_token(user.uid, email=email)}"}
requests.post(f"{server}/v1/auth/register", json={"displayName": "Dueña"}, headers=owner, timeout=10).raise_for_status()
subscription_ref(user.uid).update({"planId": "premium"})
pid = requests.post(f"{server}/v1/patients", json={"displayName": "Abuela"}, headers=owner, timeout=10).json()["id"]
get_db().collection("patients").document(pid).collection("consents").document("deteccion").set({"active": True})
node = requests.post(f"{server}/v1/patients/{pid}/nodes", json={"name": "Dormitorio"}, headers=owner, timeout=10)
node.raise_for_status()
print(pid, node.json()["credential"], owner["Authorization"])
