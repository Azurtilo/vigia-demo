"""Node delivery without camera or server: fake HTTP session and clocks."""

import threading
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone

import requests

from edge.bed import BedZone
from edge.posture import LABELS
from edge.run import (
    LEASE_SECONDS,
    OBSERVATION_RETRY_SECONDS,
    RISK_RETRY_SECONDS,
    Monitor,
    Uplink,
    args_parser,
    bed_from_args,
)
from edge.test_fall import BED, FALL, FPS, SLIDE, STILL, body, sequence

# Far from any synthetic body: the classifier answers "indeterminada".
REFERENCES = {label: [float(10 + i)] * 24 for i, label in enumerate(LABELS)}


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class Response:
    def __init__(self, status, data=None):
        self.status_code, self.data = status, data or {}

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class Server:
    """Fake edge API with the backend's event_id deduplication.

    `script` lists, per POST, "ok", "down" (no connection) or "lost" (stored
    but the answer never arrives). `hold` delays every answer by that many
    real seconds.
    """

    def __init__(self, script=(), down_gets=0, hold=0.0):
        self.script, self.down_gets, self.hold = list(script), down_gets, hold
        self.rows, self.posts = {}, []
        self.in_flight, self.answered = threading.Event(), threading.Event()

    def get(self, url, headers, timeout):
        if self.down_gets:
            self.down_gets -= 1
            raise requests.ConnectionError("sin red")
        return Response(200, {"enabled": True, "lease_seconds": 30})

    def post(self, url, headers, json, timeout):
        self.posts.append(dict(json))
        self.in_flight.set()
        if self.hold:
            time.sleep(self.hold)
        mode = self.script.pop(0) if self.script else "ok"
        if mode == "down":
            raise requests.ConnectionError("sin red")
        duplicate = json["event_id"] in self.rows
        self.rows.setdefault(json["event_id"], dict(json))
        if mode == "lost":
            raise requests.Timeout("respuesta perdida")
        self.answered.set()
        return Response(200 if duplicate else 201, {"duplicate": duplicate})


def fall_payload(observed=None):
    return {
        "event_id": str(uuid.uuid4()),
        "observed_at": (observed or datetime.now(timezone.utc)).isoformat(),
        "posture": "indeterminada",
        "confidence": 0.0,
        "model_version": "test",
        "rule_version": "fall-v1",
        "risk": "fall",
    }


def drive(uplink, clock, until, limit=200):
    """Runs worker steps on the fake clock until `until()` or the step limit."""
    for _ in range(limit):
        if until():
            return
        clock.t += max(uplink.step(), 0.01)
    raise AssertionError("El uplink no llegó al estado esperado.")


class SlowNetworkTests(unittest.TestCase):
    """QA-2026-10-22-01: a slow server must not reset the frame rules."""

    def test_fall_is_confirmed_while_the_server_takes_seconds_to_answer(self):
        for delay in (2.5, 5.0):
            with self.subTest(delay=delay):
                server = Server(hold=delay)
                uplink = Uplink("https://vigia.test", "token", session=server)
                monitor = Monitor(REFERENCES, 3600, None, uplink)
                uplink.start()
                try:
                    monitor.process(body(**FALL[0]), body(**FALL[0]), 0.0, 1.0)
                    self.assertTrue(server.in_flight.wait(2), "el envío no empezó")
                    # While the first POST is held, every frame call returns at once.
                    gaps = []
                    for i, pose in enumerate(FALL[1:], start=1):
                        started = time.monotonic()
                        monitor.process(body(**pose), body(**pose), i / FPS, 1.0)
                        gaps.append(time.monotonic() - started)
                    self.assertFalse(server.answered.is_set(), "el servidor ya respondió")
                    self.assertLess(max(gaps), monitor.fall.config.max_gap_seconds / 4)
                    falls = [p for _, p in uplink.pending if p["risk"] == "fall"]
                    self.assertEqual(len(falls), 1)
                    self.assertEqual(monitor.fall.state, "alerted")
                finally:
                    server.hold = 0.0  # only the first answer is slow
                    uplink.stop(drain_seconds=delay * 3)
                stored = [r for r in server.rows.values() if r["risk"] == "fall"]
                self.assertEqual(stored, falls)


class OutageTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()

    def test_outage_keeps_events_and_sends_them_with_original_time(self):
        server = Server(script=["down"] * 6)
        uplink = Uplink("https://vigia.test", "token", session=server, clock=self.clock)
        drive(uplink, self.clock, lambda: uplink.lease_active(self.clock()))
        fall = fall_payload()
        uplink.enqueue(fall)
        delays = []
        for _ in range(6):
            uplink.step()
            delays.append(uplink.retry_at - self.clock())
            self.clock.t = uplink.retry_at
        self.assertEqual(delays, [1, 2, 4, 8, 16, 30])  # exponential backoff, capped
        # The lease expired during the outage: capture stops, the event stays queued.
        self.assertFalse(uplink.lease_active(self.clock()))
        self.assertEqual([p for _, p in uplink.pending], [fall])
        drive(uplink, self.clock, lambda: not uplink.pending)
        self.assertTrue(uplink.lease_active(self.clock()))
        self.assertEqual(server.rows[fall["event_id"]], fall)
        self.assertEqual(server.rows[fall["event_id"]]["observed_at"], fall["observed_at"])

    def test_lease_survives_a_slow_renewal_shorter_than_its_length(self):
        server = Server(down_gets=0)
        uplink = Uplink("https://vigia.test", "token", session=server, clock=self.clock)
        uplink.step()
        self.clock.t = LEASE_SECONDS - 0.1
        self.assertTrue(uplink.lease_active(self.clock()))

    def test_risk_goes_first_and_events_expire_by_kind(self):
        server = Server(script=["down"])
        uplink = Uplink("https://vigia.test", "token", session=server, clock=self.clock)
        ordinary = {**fall_payload(), "risk": "", "rule_version": "calibrated-v1"}
        immobility = {**fall_payload(), "risk": "immobility", "posture": "supina"}
        uplink.enqueue(ordinary)
        uplink.enqueue(immobility)
        uplink.step()  # lease, then the risk is tried first and fails
        self.assertEqual(server.posts[0]["risk"], "immobility")
        self.clock.t = OBSERVATION_RETRY_SECONDS + 1
        with self.assertLogs("vigia.edge", "INFO"):
            drive(uplink, self.clock, lambda: not uplink.pending)
        self.assertNotIn(ordinary["event_id"], server.rows)
        self.assertIn(immobility["event_id"], server.rows)
        late = fall_payload()
        uplink.enqueue(late)
        self.clock.t += RISK_RETRY_SECONDS + 1
        with self.assertLogs("vigia.edge", "ERROR"):
            uplink.step()
        self.assertEqual(uplink.pending, [])

    def test_denied_node_stops_at_once_and_bad_payload_is_dropped(self):
        uplink = Uplink("https://vigia.test", "token", session=Server(), clock=self.clock)
        uplink.step()
        self.assertTrue(uplink.lease_active(self.clock()))
        uplink.session.post = lambda *a, **k: Response(403)
        uplink.enqueue(fall_payload())
        uplink.step()
        self.assertFalse(uplink.lease_active(self.clock()))
        self.assertEqual(len(uplink.pending), 1)
        uplink.session.post = lambda *a, **k: Response(400)
        self.clock.t = uplink.retry_at
        with self.assertLogs("vigia.edge", "ERROR"):
            uplink.step()
        self.assertEqual(uplink.pending, [])


class RetryTests(unittest.TestCase):
    def test_lost_answer_is_retried_with_the_same_event_and_stored_once(self):
        clock = Clock()
        server = Server(script=["lost", "lost"])
        uplink = Uplink("https://vigia.test", "token", session=server, clock=clock)
        fall = fall_payload(datetime.now(timezone.utc) - timedelta(seconds=1))
        uplink.enqueue(fall)
        drive(uplink, clock, lambda: not uplink.pending)
        self.assertEqual(len(server.posts), 3)
        self.assertTrue(all(p == fall for p in server.posts))
        self.assertEqual(list(server.rows), [fall["event_id"]])


def feed(monitor, frames, start=0.0):
    """Frames at 30 fps through Monitor.process; returns the next time."""
    now = start
    for pose in frames:
        points = body(**pose) if pose else []
        monitor.process(points, points, now, 1.0)
        now += 1 / FPS
    return now


def falls(uplink):
    return [p["rule_version"] for _, p in uplink.pending if p["risk"] == "fall"]


class BedMonitorTests(unittest.TestCase):
    """Spec 017: two fall rules, one alert per event."""

    def monitor(self, zone=BED):
        uplink = Uplink("https://vigia.test", "token", session=Server())
        return Monitor(REFERENCES, 3600, None, uplink, bed_zone=zone), uplink

    def test_without_bed_zone_spec_012_is_unchanged(self):
        monitor, uplink = self.monitor(zone=None)
        feed(monitor, FALL)
        self.assertIsNone(monitor.bed)
        self.assertEqual(falls(uplink), ["fall-v1"])
        monitor, uplink = self.monitor(zone=None)
        feed(monitor, SLIDE)
        self.assertEqual(falls(uplink), [])  # the slow slide needs the bed zone

    def test_fall_meeting_both_rules_is_sent_once(self):
        monitor, uplink = self.monitor()
        with self.assertLogs("vigia.edge", "INFO") as logs:
            feed(monitor, FALL + sequence((20, STILL), start=FALL[-1]))
        self.assertEqual(falls(uplink), ["fall-v1"])
        self.assertTrue(any("ya avisada" in line and "fall-bed-v1" in line for line in logs.output))

    def test_slow_slide_is_sent_by_the_bed_rule_without_coordinates_in_the_log(self):
        monitor, uplink = self.monitor()
        with self.assertLogs("vigia.edge", "WARNING") as logs:
            feed(monitor, SLIDE)
        self.assertEqual(falls(uplink), ["fall-bed-v1"])
        line = next(line for line in logs.output if "fall-bed-v1" in line)
        self.assertIn("event_id=", line)
        self.assertNotIn("'x'", line)
        self.assertNotIn("0.6", line)

    def test_two_falls_with_three_seconds_upright_between(self):
        monitor, uplink = self.monitor()
        upright = sequence((1.5, FALL[0]), (4, STILL), start=FALL[-1])
        feed(monitor, FALL + upright + FALL)
        self.assertEqual(len(falls(uplink)), 2)

    def test_lying_again_without_rearm_is_the_same_event(self):
        monitor, uplink = self.monitor()
        now = feed(monitor, FALL)
        # Upright for single frames between empty ones, then down again.
        flicker = [FALL[0] if k % 10 == 0 else None for k in range(5 * FPS)]
        feed(monitor, flicker + sequence((1, FALL[-1]), (8, STILL), start=FALL[0]), now)
        self.assertEqual(len(falls(uplink)), 1)

    def test_invalid_bed_arguments_stop_at_start(self):
        parser = args_parser()
        for argv in (["--bed-lying-angle", "120"], ["--bed-config", "no-existe.json"]):
            with self.subTest(argv), self.assertRaises(SystemExit) as stop:
                bed_from_args(parser.parse_args(["--references", "r.json", *argv]))
            self.assertIn("Configuración de cama inválida", str(stop.exception))
        zone, config = bed_from_args(parser.parse_args(["--references", "r.json"]))
        self.assertIsNone(zone)
        self.assertEqual(config.lying_seconds, 5.0)
        self.assertIsInstance(BED, BedZone)


if __name__ == "__main__":
    unittest.main()
