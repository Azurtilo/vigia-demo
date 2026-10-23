"""Deterministic fall rule over a time window of MediaPipe landmarks. No clinical claims.

Uses normalized image landmarks (pose_landmarks), not world landmarks: world
landmarks are centred on the hips, so the hip height this rule needs is always ~0.
"""

import dataclasses
import json
import math
from collections import deque
from pathlib import Path

SHOULDERS, HIPS = (11, 12), (23, 24)


@dataclasses.dataclass(frozen=True)
class FallConfig:
    # Lengths are in torso lengths (shoulder midpoint to hip midpoint) so the
    # thresholds do not depend on the distance to the camera.
    window_seconds: float = 1.5
    min_interval_seconds: float = 0.2
    descent_velocity: float = 1.5
    min_drop: float = 0.8
    trunk_angle: float = 60.0
    aspect_ratio: float = 1.0
    aspect_change: float = 1.5
    confirm_seconds: float = 5.0
    recover_angle: float = 45.0
    stay_down_drop: float = 0.5
    max_gap_seconds: float = 2.0
    min_visibility: float = 0.5
    floor_hip_y: float | None = None

    def __post_init__(self):
        for f in dataclasses.fields(self):
            value = getattr(self, f.name)
            if value is None and f.name == "floor_hip_y":
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{f.name} debe ser numérico.")
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{f.name} debe ser finito y mayor que cero.")
        if self.min_interval_seconds >= self.window_seconds:
            raise ValueError("min_interval_seconds debe ser menor que window_seconds.")
        if not self.recover_angle < self.trunk_angle <= 90:
            raise ValueError("Se exige recover_angle < trunk_angle <= 90.")
        if self.stay_down_drop > self.min_drop:
            raise ValueError("stay_down_drop no puede superar min_drop.")
        if self.aspect_change < 1:
            raise ValueError("aspect_change debe ser al menos 1.")
        if self.min_visibility > 1 or (
            self.floor_hip_y is not None and self.floor_hip_y > 1
        ):
            raise ValueError("min_visibility y floor_hip_y van de 0 a 1.")

    @classmethod
    def from_file(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        names = {f.name for f in dataclasses.fields(cls)}
        if not isinstance(data, dict) or set(data) - names:
            raise ValueError(
                f"Configuración de caídas inválida; claves admitidas: {sorted(names)}."
            )
        return cls(**data)


def add_arguments(parser):
    group = parser.add_argument_group("detección de caídas")
    group.add_argument("--fall-config", help="JSON local con umbrales de caída")
    for f in dataclasses.fields(FallConfig):
        group.add_argument(
            "--fall-" + f.name.replace("_", "-"),
            dest="fall_" + f.name,
            type=float,
            help=f"por defecto {f.default}",
        )


def config_from_args(args):
    """File values first, then explicit --fall-* arguments; validation re-runs."""
    base = FallConfig.from_file(args.fall_config) if args.fall_config else FallConfig()
    overrides = {
        f.name: getattr(args, "fall_" + f.name)
        for f in dataclasses.fields(FallConfig)
        if getattr(args, "fall_" + f.name) is not None
    }
    return dataclasses.replace(base, **overrides)


def frame_features(landmarks, frame_aspect=1.0, min_visibility=0.5):
    if len(landmarks) != 33:
        return None

    def usable(p):
        return min(p.get("visibility", 0), p.get("presence", 0)) >= min_visibility and all(
            math.isfinite(float(p.get(k, math.nan))) for k in ("x", "y")
        )

    if not all(usable(landmarks[i]) for i in SHOULDERS + HIPS):
        return None
    # Normalized x and y use different units; scale x to image heights.
    points = [(p["x"] * frame_aspect, p["y"]) for p in landmarks if usable(p)]

    def mid(a, b):
        return (
            (landmarks[a]["x"] + landmarks[b]["x"]) * frame_aspect / 2,
            (landmarks[a]["y"] + landmarks[b]["y"]) / 2,
        )

    hip, shoulder = mid(*HIPS), mid(*SHOULDERS)
    dx, dy = shoulder[0] - hip[0], shoulder[1] - hip[1]
    torso = math.hypot(dx, dy)
    if torso < 0.02:
        return None
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return {
        "hip_y": hip[1],
        "torso": torso,
        # 0 degrees upright, 90 horizontal; image y grows downwards.
        "angle": math.degrees(math.acos(max(-1.0, min(1.0, -dy / torso)))),
        "aspect": (max(xs) - min(xs)) / max(max(ys) - min(ys), 1e-3),
    }


class FallDetector:
    """idle -> confirming (impact seen) -> alerted (fall emitted once)."""

    def __init__(self, config=None, frame_aspect=1.0):
        if not math.isfinite(frame_aspect) or frame_aspect <= 0:
            raise ValueError("La relación de aspecto del cuadro debe ser positiva.")
        self.config, self.frame_aspect = config or FallConfig(), frame_aspect
        self.last_time = None
        self.reset()

    def reset(self):
        self.history = deque()
        self.state, self.last_valid = "idle", None
        self.impact_at, self.reference_y, self.scale = None, None, None

    def observe(self, landmarks, now):
        c = self.config
        # A gap resets evidence: a camera that stopped cannot confirm a fall.
        if self.last_time is not None and now - self.last_time > c.max_gap_seconds:
            self.reset()
        self.last_time = now
        f = frame_features(landmarks, self.frame_aspect, c.min_visibility)
        if f is None:
            if self.last_valid is not None and now - self.last_valid > c.max_gap_seconds:
                self.reset()
            return ""
        self.last_valid = now
        self.history.append((now, f))
        while now - self.history[0][0] > c.window_seconds:
            self.history.popleft()
        if self.state == "idle":
            if self._impact(now, f):
                self.state, self.impact_at = "confirming", now
            return ""
        down = self._down(f)
        if self.state == "confirming":
            if not down:
                self.state = "idle"
            elif now - self.impact_at >= c.confirm_seconds:
                self.state = "alerted"
                return "fall"
            return ""
        if not down:
            self.state = "idle"  # got up; a new fall needs a new impact
        return ""

    def _impact(self, now, f):
        c = self.config
        if f["angle"] < c.trunk_angle or f["aspect"] < c.aspect_ratio:
            return False
        scale = max(h["torso"] for _, h in self.history)
        top = min(h["hip_y"] for _, h in self.history)
        velocity = max(
            (
                (f["hip_y"] - h["hip_y"]) / (now - t)
                for t, h in self.history
                if now - t >= c.min_interval_seconds
            ),
            default=0.0,
        )
        lowest_aspect = min(h["aspect"] for _, h in self.history)
        if (
            (f["hip_y"] - top) / scale >= c.min_drop
            and velocity / scale >= c.descent_velocity
            and f["aspect"] / max(lowest_aspect, 1e-6) >= c.aspect_change
        ):
            self.reference_y, self.scale = top, scale
            return True
        return False

    def _down(self, f):
        c = self.config
        return (
            f["angle"] >= c.recover_angle
            and (f["hip_y"] - self.reference_y) / self.scale >= c.stay_down_drop
            and (c.floor_hip_y is None or f["hip_y"] >= c.floor_hip_y)
        )


if __name__ == "__main__":
    # Print the documented defaults: python -m edge.fall
    print(json.dumps(dataclasses.asdict(FallConfig()), indent=2))
