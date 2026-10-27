"""Synthetic side-view sequences at 30 fps. They test the rule, not real-world accuracy."""

import argparse
import json
import math
import tempfile
import unittest
from pathlib import Path

from edge.bed import BedConfig, BedFallRule, BedZone
from edge.bed import add_arguments as add_bed_arguments
from edge.bed import config_from_args as bed_config_from_args
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


# Spec 017: bed on the left of the image, person lying in it with the head to the right.
BED = BedZone([[0.05, 0.5], [0.4, 0.5], [0.4, 0.75], [0.05, 0.75]])
IN_BED = {"hx": 0.15, "hy": 0.62, "trunk": 90, "thigh": 90, "shank": 90}
FLOOR_OUT = {"hx": 0.6, "hy": 0.85, "trunk": 85, "thigh": 85, "shank": 85}
UP_OUT = {"hx": 0.7, "hy": 0.5, "trunk": 0, "thigh": 0, "shank": 0}
SLIDE = sequence((1, STILL), (3, FLOOR_OUT), (8, STILL), start=IN_BED)


def hide(points, keep=None, drop=()):
    """Covered landmarks: visibility 0 for `drop`, or for all but `keep`."""
    return [
        {**p, "visibility": 0.0}
        if (keep is not None and i not in keep) or i in drop
        else p
        for i, p in enumerate(points)
    ]


def run_bed(frames, rule=None, missing=(), cover=None):
    """cover(now, points) -> points lets a test hide landmarks over time."""
    rule = rule or BedFallRule(BED)
    falls, results = [], []
    for i, pose in enumerate(frames):
        now = i / FPS
        points = [] if any(a <= now < b for a, b in missing) else body(**pose)
        if points and cover:
            points = cover(now, points)
        result = rule.observe(points, now)
        results.append(result)
        if result == "fall":
            falls.append(now)
    return falls, results


class BedZoneTests(unittest.TestCase):
    def test_invalid_zones_are_rejected(self):
        for bad in (
            [[0.1, 0.1], [0.5, 0.1]],
            [[0.1, 0.1], [0.5, 0.1], [0.5, 1.2]],
            [[0.1, 0.1], [0.5, 0.1], [True, 0.5]],
            [[0.1, 0.1], [0.5, 0.1], [0.5, math.nan]],
            [[0.1, 0.1], [0.3, 0.3], [0.5, 0.5]],  # collinear: no area
            [[0.1 * i, 0.1] for i in range(9)],
            "cama",
        ):
            with self.subTest(bad), self.assertRaises(ValueError):
                BedZone(bad)

    def test_file_needs_only_the_bed_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cama.json"
            path.write_text(json.dumps(BED.to_json()))
            self.assertEqual(BedZone.from_file(path).points, BED.points)
            path.write_text(json.dumps({**BED.to_json(), "foto": "x"}))
            with self.assertRaises(ValueError):
                BedZone.from_file(path)

    def test_corners_in_any_order_and_border_inside(self):
        crossed = BedZone([[0.2, 0.2], [0.8, 0.8], [0.8, 0.2], [0.2, 0.8]])
        self.assertAlmostEqual(crossed.area(), 0.36)
        self.assertTrue(crossed.contains(0.5, 0.5))
        self.assertTrue(crossed.contains(0.5, 0.25))
        self.assertTrue(BED.contains(0.4, 0.6))  # on the edge
        self.assertTrue(BED.contains(0.05, 0.5))  # on a corner
        self.assertFalse(BED.contains(0.41, 0.6))

    def test_config_arguments_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "umbrales.json"
            path.write_text(json.dumps({"lying_seconds": 4, "smoothing_frames": 5}))
            parser = argparse.ArgumentParser()
            add_bed_arguments(parser)
            args = parser.parse_args(["--bed-settings", str(path), "--bed-lying-seconds", "3"])
            config = bed_config_from_args(args)
            self.assertEqual((config.lying_seconds, config.smoothing_frames), (3, 5))
            path.write_text(json.dumps({"desconocida": 1}))
            with self.assertRaises(ValueError):
                bed_config_from_args(parser.parse_args(["--bed-settings", str(path)]))
        for bad in ({"lying_angle": 95}, {"smoothing_frames": 2.5}, {"lying_seconds": -1},
                    {"max_track_speed": math.inf}, {"rearm_upright_seconds": True}):
            with self.subTest(bad), self.assertRaises((ValueError, TypeError)):
                BedConfig(**bad)


class BedFallTests(unittest.TestCase):
    def test_slow_slide_out_of_bed_is_a_fall_the_impact_rule_misses(self):
        falls, _ = run_bed(SLIDE)
        self.assertEqual(len(falls), 1)
        # The hips leave the bed at about 2.7 s; then 5 s lying outside.
        self.assertTrue(7.5 <= falls[0] <= 8.5, falls)
        self.assertEqual(run(SLIDE), [])

    def test_upright_or_sitting_outside_the_bed_is_not_a_fall(self):
        edge = {"hx": 0.3, "hy": 0.6, "trunk": 10, "thigh": 60, "shank": 0}
        chair = {"hx": 0.7, "hy": 0.68, "trunk": 15, "thigh": 80, "shank": 0}
        frames = sequence((1, STILL), (1, edge), (2, UP_OUT), (1, chair), (60, STILL), start=IN_BED)
        self.assertEqual(run_bed(frames)[0], [])

    def test_lying_outside_briefly_and_getting_up_is_not_a_fall(self):
        frames = sequence((1, STILL), (1, FLOOR_OUT), (2.5, STILL), (1.5, UP_OUT), (10, STILL),
                          start=UP_OUT)
        self.assertEqual(run_bed(frames)[0], [])

    def test_lying_outside_long_after_walking_is_a_fall(self):
        frames = sequence((1, STILL), (1, FLOOR_OUT), (8, STILL), start=UP_OUT)
        self.assertEqual(len(run_bed(frames)[0]), 1)

    def test_shape_appearing_on_the_floor_is_treated_as_no_person(self):
        floor = sequence((30, STILL), start=FLOOR_OUT)
        falls, results = run_bed(floor, missing=[(0, 2)])
        self.assertEqual(falls, [])
        self.assertEqual(set(results), {"no_person"})
        # Seen upright, then lost longer than the tracking gap: a new detection.
        frames = sequence((2, STILL), (0.1, FLOOR_OUT), (30, STILL), start=UP_OUT)
        self.assertEqual(run_bed(frames, missing=[(1.5, 3.5)])[0], [])

    def test_teleport_breaks_the_track(self):
        frames = sequence((2, STILL), start=UP_OUT) + sequence((10, STILL), start=FLOOR_OUT)
        falls, results = run_bed(frames)
        self.assertEqual(falls, [])
        self.assertEqual(results[-1], "no_person")

    def test_covered_hips_fall_back_to_shoulders_without_a_jump(self):
        def covered(now, points):
            return hide(points, drop=(23, 24)) if now >= 3 else points

        self.assertEqual(len(run_bed(SLIDE, cover=covered)[0]), 1)

    def test_only_the_head_outside_the_bed_is_unknown(self):
        def head_only(now, points):
            return hide(points, keep=(0, 7, 8)) if now >= 2 else points

        falls, results = run_bed(SLIDE, cover=head_only)
        self.assertEqual(falls, [])
        self.assertEqual(results[-1], "no_person")

    def test_back_in_bed_or_upright_rearms(self):
        rule = BedFallRule(BED)
        frames = SLIDE + sequence((1, UP_OUT), (4, STILL), (1, FLOOR_OUT), (8, STILL),
                                  start=SLIDE[-1])
        self.assertEqual(len(run_bed(frames, rule)[0]), 2)
        # Isolated upright frames between empty ones, for 5 s, do not rearm:
        # the person lying down again right after is the same event.
        rule = BedFallRule(BED)
        falls, _ = run_bed(SLIDE, rule)
        now = len(SLIDE) / FPS
        for k in range(5 * FPS):
            now += 1 / FPS
            rule.observe(body(**UP_OUT) if k % 10 == 0 else [], now)
        for pose in sequence((1, FLOOR_OUT), (8, STILL), start=UP_OUT):
            now += 1 / FPS
            if rule.observe(body(**pose), now) == "fall":
                falls.append(now)
        self.assertEqual(len(falls), 1)


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
