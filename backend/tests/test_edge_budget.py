"""Cuota gratuita de Firestore con un nodo renovando cada 10 s (RF-019-11, D-095).

Sin emuladores: se simula un día con un reloj falso y se cuentan las lecturas y escrituras que
haría el backend. Spark permite 50.000 lecturas y 20.000 escrituras diarias.
"""

import pytest

from app.services import edge_cache, nodes

DAY_SECONDS = 24 * 60 * 60
RENEW_EVERY = 10  # edge/run.py: LEASE_REFRESH_SECONDS
READS_PER_LOAD = 5  # nodo, paciente, suscripción, plan y consentimiento


@pytest.fixture
def day(monkeypatch):
    now = {"t": 0.0}
    counts = {"loads": 0, "writes": 0}

    def load(credential_hash):
        counts["loads"] += 1
        return edge_cache.NodeAuth("n1", "p1", "u1", "Cámara", True, edge_cache.clock())

    monkeypatch.setattr(edge_cache, "clock", lambda: now["t"])
    monkeypatch.setattr(nodes, "_load", load)
    monkeypatch.setattr(nodes, "_write_node", lambda node_id, changes: counts.__setitem__("writes", counts["writes"] + 1))
    edge_cache.forget(everything=True)
    yield now, counts
    edge_cache.forget(everything=True)


def test_one_node_renewing_every_10_s_stays_within_the_free_quota(day):
    now, counts = day
    renewals = DAY_SECONDS // RENEW_EVERY

    for i in range(renewals):
        now["t"] = i * RENEW_EVERY
        nodes.edge_status("Bearer token-del-nodo", [("monitor_state", "normal")])

    assert renewals == 8640
    assert counts["loads"] <= DAY_SECONDS // edge_cache.AUTH_CACHE_SECONDS + 1
    assert counts["writes"] <= DAY_SECONDS // nodes.SEEN_WRITE_SECONDS + 1
    # Sin caché serían ~43.000 lecturas y 8.640 escrituras solo por este nodo.
    assert counts["loads"] * READS_PER_LOAD < 10_000 and counts["writes"] < 3_000


def test_a_monitor_state_change_is_written_at_once(day):
    now, counts = day
    nodes.edge_status("Bearer t", [("monitor_state", "normal")])
    now["t"] = 10
    nodes.edge_status("Bearer t", [("monitor_state", "normal")])
    assert counts["writes"] == 1

    now["t"] = 20
    nodes.edge_status("Bearer t", [("monitor_state", "sin_imagen")])

    assert counts["writes"] == 2


def test_forgetting_during_a_load_does_not_cache_a_stale_decision(day, monkeypatch):
    _, counts = day
    original = nodes._load

    def load_while_revoked(credential_hash):
        entry = original(credential_hash)
        edge_cache.forget(patient_id="p1")  # la revocación llega mientras se leía
        return entry

    monkeypatch.setattr(nodes, "_load", load_while_revoked)
    nodes.edge_status("Bearer t", [])
    nodes.edge_status("Bearer t", [])

    assert counts["loads"] == 2
