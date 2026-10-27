"""Node delivery without camera or server: fake HTTP session and clocks."""

import threading
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone

import requests

from edge import monitoring
from edge.bed import BedZone
from edge.monitoring import Camera, MonitorConfig, MonitorStatus
from edge.posture import LABELS
from edge.run import (
    LEASE_SECONDS,
    OBSERVATION_RETRY_SECONDS,
    RISK_RETRY_SECONDS,
    Monitor,
    Uplink,
    args_parser,
    bed_from_args,
    monitor_config_from_args,
)
from edge.test_fall import (
    BED,
    FALL,
    FLOOR_OUT,
    FPS,
    SLIDE,
    STILL,
    UP_OUT,
    body,
    sequence,
)

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
        self.rows, self.posts, self.renewals = {}, [], []
        self.in_flight, self.answered = threading.Event(), threading.Event()

    def get(self, url, headers, timeout, params=None):
        self.renewals.append(params)
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


def states(status, frames):
    """frames: (now, person, brightness), or (now, None) for a tick; returns changes."""
    out = []
    for now, person, *light in frames:
        if person is None:
            changed = status.tick(now)
        else:
            changed = status.frame(now, person, light[0] if light else None)
        if changed:
            out.append((round(now, 2), changed))
    return out


def every(start, end, person, light=None):
    return [(start + k / FPS, person, light) for k in range(round((end - start) * FPS))]


class MonitorStatusTests(unittest.TestCase):
    """Spec 017: the node says when it cannot watch, instead of failing silently."""

    def test_person_lost_after_being_seen_and_back(self):
        frames = every(0, 2, True) + every(2, 14, False) + every(14, 15, True)
        changes = states(MonitorStatus(), frames)
        self.assertEqual([s for _, s in changes], ["persona_no_visible", "normal"])
        self.assertAlmostEqual(changes[0][0], 2 - 1 / FPS + 10, delta=0.05)

    def test_never_seen_is_not_lost(self):
        self.assertEqual(states(MonitorStatus(), every(0, 60, False)), [])

    def test_no_image_while_frames_stop_and_recovery(self):
        frames = every(0, 2, True) + [(2 + k * 0.2, None) for k in range(60)]
        frames += every(14.5, 15, True)
        changes = states(MonitorStatus(), frames)
        self.assertEqual([s for _, s in changes], ["sin_imagen", "normal"])
        self.assertAlmostEqual(changes[0][0], 2 - 1 / FPS + 10, delta=0.25)

    def test_no_frame_at_all_from_start(self):
        self.assertEqual(states(MonitorStatus(), [(t, None) for t in range(12)]),
                         [(10, "sin_imagen")])

    def test_low_light_with_hysteresis(self):
        frames = every(0, 6, False, 0.05) + every(6, 12, False, 0.20)
        self.assertEqual([s for _, s in states(MonitorStatus(), frames)], ["poca_luz", "normal"])
        # Oscillating around the minimum never switches from normal...
        wobble = [(k / FPS, False, 0.11 if k % 2 else 0.13) for k in range(20 * FPS)]
        self.assertEqual(states(MonitorStatus(), wobble), [])
        # ...and, once dark, 0.13 is not enough light to recover (needs 0.156).
        status = MonitorStatus()
        states(status, every(0, 6, False, 0.05))
        self.assertEqual(states(status, every(6, 20, False, 0.13)), [])
        self.assertEqual(status.state, "poca_luz")

    def test_priority_no_image_then_low_light_then_lost(self):
        status = MonitorStatus()
        states(status, every(0, 1, True, 0.5))
        changes = states(status, every(1, 13, False, 0.05))
        self.assertEqual([s for _, s in changes], ["poca_luz"])  # lost is hidden by it
        changes = states(status, [(13 + k, None) for k in range(12)])
        self.assertEqual([s for _, s in changes], ["sin_imagen"])

    def test_config_validation(self):
        for bad in ({"lost_seconds": 0}, {"min_brightness": 0.9}, {"no_image_seconds": True}):
            with self.subTest(bad), self.assertRaises((ValueError, TypeError)):
                MonitorConfig(**bad)
        args = args_parser().parse_args(["--references", "r", "--monitor-lost-seconds", "20"])
        self.assertEqual(monitor_config_from_args(args).lost_seconds, 20)
        with self.assertRaises(SystemExit):
            monitor_config_from_args(
                args_parser().parse_args(["--references", "r", "--monitor-min-brightness", "2"])
            )


class FakeCapture:
    def __init__(self, frames):
        self.frames, self.released = frames, False

    def read(self):
        return (True, "cuadro") if self.frames.pop(0) else (False, None)

    def release(self):
        self.released = True


class CameraTests(unittest.TestCase):
    def test_live_camera_is_reopened_with_backoff_and_never_ends(self):
        clock, opened = Clock(), []
        # First capture: 2 frames then failure; three opens fail; the fifth works.
        script = [[1, 1, 0], [0], [0], [0], [1] * 10]

        def opener(source):
            opened.append(round(clock(), 1))
            return FakeCapture(script.pop(0))

        camera = Camera(0, opener, clock)
        got = []
        for _ in range(400):
            got.append(camera.read())
            clock.t += 0.25  # exact in binary: no float drift
            if len(opened) == 5 and got[-1]:
                break
        self.assertFalse(camera.ended)
        self.assertEqual(got[:2], ["cuadro", "cuadro"])
        self.assertEqual(got[-1], "cuadro")
        # Failure at 0.5 s, then waits of 1, 2, 4 and 8 s before each reopening.
        self.assertEqual(opened, [0.0, 1.5, 3.5, 7.5, 15.5])
        self.assertEqual(camera.backoff, 1.0)  # reset once frames come back

    def test_video_file_ends(self):
        camera = Camera("video.mp4", lambda s: FakeCapture([1, 0]), Clock())
        self.assertEqual(camera.read(), "cuadro")
        self.assertIsNone(camera.read())
        self.assertTrue(camera.ended)


class MonitorStateTests(unittest.TestCase):
    def monitor(self, zone=None):
        uplink = Uplink("https://vigia.test", "token", session=Server())
        return Monitor(REFERENCES, 3600, None, uplink, bed_zone=zone)

    def test_two_people_in_view_are_not_lost(self):
        monitor = self.monitor()
        feed(monitor, sequence((1, STILL), start=UP_OUT))
        for k in range(15 * FPS):
            monitor.process([], [], 1 + k / FPS, 1.0, people=2)
        self.assertEqual(monitor.status.state, "normal")
        with self.assertLogs("vigia.edge", "WARNING") as logs:
            for k in range(11 * FPS):
                monitor.process([], [], 17 + k / FPS, 1.0, people=0)
        self.assertEqual(monitor.status.state, "persona_no_visible")
        self.assertIn("Estado de monitoreo: persona_no_visible", logs.output[-1])

    def test_sheet_on_the_floor_counts_as_no_person(self):
        monitor = self.monitor(zone=BED)
        now = feed(monitor, sequence((1, STILL), start=UP_OUT))
        # The person vanishes and a "lying" shape appears without a track.
        feed(monitor, [None] * (2 * FPS) + sequence((12, STILL), start=FLOOR_OUT), now)
        self.assertEqual(monitor.status.state, "persona_no_visible")
        self.assertEqual(falls(monitor.uplink), [])

    def test_lease_pause_is_not_a_blind_camera(self):
        monitor = self.monitor()
        now = feed(monitor, sequence((1, STILL), start=UP_OUT))
        monitor.reset()  # what main() does when the lease is denied
        monitor.tick(now + 20)
        monitor.tick(now + 25)
        self.assertEqual(monitor.status.state, "normal")
        monitor.tick(now + 31)
        self.assertEqual(monitor.status.state, monitoring.NO_IMAGE)


class MonitorStateUplinkTests(unittest.TestCase):
    """Spec 017, D-073: the state rides on the lease renewal."""

    def test_every_renewal_reports_the_state_and_a_change_goes_at_once(self):
        clock, server = Clock(), Server()
        uplink = Uplink("https://vigia.test", "token", session=server, clock=clock)
        uplink.step()
        self.assertEqual(server.renewals, [{"monitor_state": "normal"}])
        clock.t = 2.0  # well before the next scheduled renewal (10 s)
        uplink.set_monitor_state("sin_imagen")
        uplink.step()
        self.assertEqual(server.renewals[-1], {"monitor_state": "sin_imagen"})
        uplink.set_monitor_state("sin_imagen")  # unchanged: no extra renewal
        clock.t = 3.0
        uplink.step()
        self.assertEqual(len(server.renewals), 2)
        self.assertTrue(uplink.lease_active(clock()))  # an old server ignores it

    def test_only_known_states_are_sent(self):
        uplink = Uplink("https://vigia.test", "token", session=Server())
        for bad in ("caida", "", None, "Normal"):
            with self.subTest(bad), self.assertRaises(ValueError):
                uplink.set_monitor_state(bad)
        self.assertEqual(set(monitoring.STATES),
                         {"normal", "persona_no_visible", "sin_imagen", "poca_luz"})

    def test_monitor_passes_changes_and_a_pause_returns_to_normal(self):
        uplink = Uplink("https://vigia.test", "token", session=Server())
        monitor = Monitor(REFERENCES, 3600, None, uplink)
        now = feed(monitor, sequence((1, STILL), start=UP_OUT))
        with self.assertLogs("vigia.edge", "WARNING"):
            monitor.tick(now + 11)
        self.assertEqual(uplink.monitor_state, "sin_imagen")
        monitor.reset()
        self.assertEqual(uplink.monitor_state, "normal")


if __name__ == "__main__":
    unittest.main()
