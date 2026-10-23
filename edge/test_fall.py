"""Synthetic side-view sequences at 30 fps. They test the rule, not real-world accuracy."""

import argparse
import json
import math
import tempfile
import unittest
from pathlib import Path

from edge.fall import FallConfig, FallDetector, add_arguments, config_from_args
from edge.metrics import LatencyStats

FPS = 30
TORSO, HEAD, THIGH, SHANK = 0.22, 0.08, 0.2, 0.2
STANDING = {"hx": 0.5, "hy": 0.5, "trunk": 0, "thigh": 0, "shank": 0}


def body(hx, hy, trunk, thigh, shank, aspect=1.0):
    """33 landmarks from hip position and segment angles (degrees from vertical)."""
    t, th, sh = (math.radians(a) for a in (trunk, thigh, shank))
    shoulder = (hx + TORSO * math.sin(t), hy - TORSO * math.cos(t))
    head = (shoulder[0] + HEAD * math.sin(t), shoulder[1] - HEAD * math.cos(t))
    elbow = ((hx + shoulder[0]) / 2, (hy + shoulder[1]) / 2)
    knee = (hx + THIGH * math.sin(th), hy + THIGH * math.cos(th))
    ankle = (knee[0] + SHANK * math.sin(sh), knee[1] + SHANK * math.cos(sh))
    where = {i: head for i in range(11)}
    where.update({11: shoulder, 12: shoulder, 13: elbow, 14: elbow, 23: (hx, hy), 24: (hx, hy)})
    where.update({i: (hx, hy) for i in range(15, 23)})  # wrists and hands by the hips
    where.update({25: knee, 26: knee})
    where.update({i: ankle for i in range(27, 33)})
    points = []
    for i in range(33):
        x, y = where[i]
        side = 0.03 if i % 2 else -0.03  # left/right width of the silhouette
        points.append(
            {"x": (x + side) / aspect, "y": y, "z": 0.0, "visibility": 1.0, "presence": 1.0}
        )
    return points


def sequence(*steps, start=STANDING):
    """steps: (seconds, pose) pairs, linearly interpolated from the previous pose."""
    frames, pose = [dict(start)], dict(start)
    for seconds, target in steps:
        target = {**pose, **target}
        n = max(1, round(seconds * FPS))
        for k in range(1, n + 1):
            frames.append({key: pose[key] + (target[key] - pose[key]) * k / n for key in pose})
        pose = target
    return frames


def run(frames, detector=None, aspect=1.0, missing=()):
    detector = detector or FallDetector()
    events = []
    for i, pose in enumerate(frames):
        now = i / FPS
        landmarks = [] if any(a <= now < b for a, b in missing) else body(**pose, aspect=aspect)
        if detector.observe(landmarks, now) == "fall":
            events.append((now, detector.impact_at))
    return events


FLOOR = {"hy": 0.85, "trunk": 85, "thigh": -85, "shank": -85}
STILL = {}
FALL = sequence((1, STILL), (0.6, FLOOR), (8, STILL))


class FallTests(unittest.TestCase):
    def test_fall_is_emitted_once_after_confirmation(self):
        events = run(FALL)
        self.assertEqual(len(events), 1)
        emitted, impact = events[0]
        self.assertGreaterEqual(emitted - impact, FallConfig().confirm_seconds)
        self.assertLess(emitted - 1.0, FallConfig().confirm_seconds + 1.0)

    def test_fall_stays_single_while_lying_long(self):
        self.assertEqual(len(run(sequence((1, STILL), (0.6, FLOOR), (30, STILL)))), 1)

    def test_widescreen_coordinates_are_scaled(self):
        self.assertEqual(len(run(FALL, FallDetector(frame_aspect=16 / 9), aspect=16 / 9)), 1)

    def test_getting_up_cancels(self):
        frames = sequence((1, STILL), (0.6, FLOOR), (2, STILL), (1.5, STANDING), (8, STILL))
        self.assertEqual(run(frames), [])

    def test_short_occlusion_is_tolerated_long_gap_cancels(self):
        self.assertEqual(len(run(FALL, missing=[(3, 4)])), 1)
        self.assertEqual(run(FALL, missing=[(3, 6)]), [])

    def test_no_signal_never_alerts(self):
        detector = FallDetector()
        self.assertTrue(all(detector.observe([], i / FPS) == "" for i in range(600)))

    def test_floor_calibration_blocks_falls_above_it(self):
        config = FallConfig(floor_hip_y=0.9)
        self.assertEqual(run(FALL, FallDetector(config)), [])
        self.assertEqual(len(run(FALL, FallDetector(FallConfig(floor_hip_y=0.8)))), 1)

    def test_daily_activities_do_not_alert(self):
        chair = {"hy": 0.68, "trunk": 15, "thigh": 80, "shank": 0}
        squat = {"hy": 0.78, "trunk": 40, "thigh": 100, "shank": -30}
        bend = {"hy": 0.52, "trunk": 85}
        bed_edge = {"hy": 0.6, "trunk": 10, "thigh": 60, "shank": 0}
        in_bed = {"hy": 0.62, "trunk": -90, "thigh": 90, "shank": 90}
        cases = {
            "sentarse rápido": sequence((1, STILL), (0.6, chair), (10, STILL)),
            "agacharse en sentadilla": sequence((1, STILL), (0.8, squat), (3, STILL), (1, STANDING)),
            "inclinarse a recoger": sequence((1, STILL), (1, bend), (3, STILL), (1, STANDING)),
            "acostarse en la cama": sequence((1, STILL), (1, bed_edge), (2, STILL), (2, in_bed), (30, STILL)),
            "dejarse caer en la cama": sequence((1, STILL), (1, bed_edge), (0.5, STILL), (0.4, in_bed), (30, STILL)),
        }
        for name, frames in cases.items():
            with self.subTest(name):
                self.assertEqual(run(frames), [])

    def test_each_impact_condition_is_required(self):
        for override in (
            {"descent_velocity": 5},
            {"min_drop": 2, "stay_down_drop": 0.5},
            {"trunk_angle": 89},
            {"aspect_ratio": 50},
            {"aspect_change": 500},
        ):
            with self.subTest(override):
                self.assertEqual(run(FALL, FallDetector(FallConfig(**override))), [])

    def test_config_file_arguments_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "caidas.json"
            path.write_text(json.dumps({"confirm_seconds": 3, "trunk_angle": 70}))
            parser = argparse.ArgumentParser()
            add_arguments(parser)
            args = parser.parse_args(["--fall-config", str(path), "--fall-trunk-angle", "65"])
            config = config_from_args(args)
            self.assertEqual((config.confirm_seconds, config.trunk_angle), (3, 65))
            path.write_text(json.dumps({"unknown": 1}))
            with self.assertRaises(ValueError):
                FallConfig.from_file(path)
        for bad in ({"confirm_seconds": -1}, {"recover_angle": 70}, {"min_visibility": 2},
                    {"window_seconds": math.nan}, {"trunk_angle": True}):
            with self.subTest(bad), self.assertRaises((ValueError, TypeError)):
                FallConfig(**bad)


class MetricsTests(unittest.TestCase):
    def test_mean_p95_and_max(self):
        stats = LatencyStats()
        self.assertIsNone(stats.summary())
        for ms in range(1, 101):
            stats.add(ms)
        self.assertEqual(
            stats.summary(), {"frames": 100, "mean_ms": 50.5, "p95_ms": 95, "max_ms": 100}
        )
        stats.reset()
        self.assertIsNone(stats.summary())
