"""Usa el cliente real del nodo (edge.run.Uplink, sin cambios) contra el backend FastAPI local.

Uso (desde la raíz del repo, con .venv-edge-win):
    python backend/scripts/smoke_edge_uplink.py <server> <token>
Imprime si el nodo obtuvo su permiso de captura y si quedaron observaciones sin entregar.
"""

import os
import sys
import time
import uuid
from datetime import UTC, datetime

sys.path.insert(0, os.getcwd())

from edge.run import Uplink  # noqa: E402

server, token = sys.argv[1], sys.argv[2]
uplink = Uplink(server, token)
fall = {
    "event_id": str(uuid.uuid4()),
    "observed_at": datetime.now(UTC).isoformat(),
    "posture": "indeterminada",
    "confidence": 0.88,
    "model_version": "pose_landmarker_lite",
    "rule_version": "fall-v1",
    "risk": "fall",
}
uplink.set_monitor_state("persona_no_visible")
uplink.enqueue(fall)
deadline = time.monotonic() + 15
while uplink.pending and time.monotonic() < deadline:
    time.sleep(min(uplink.step(), 0.5))
print("lease_activo" if uplink.lease_active(time.monotonic()) else "sin_lease", "pendientes=%d" % len(uplink.pending), fall["event_id"])
