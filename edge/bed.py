"""Bed zone and the "lying outside the bed" fall rule (spec 017). No clinical claims.

Complements the impact rule of edge/fall.py: a person who slides slowly out of
bed never shows a fast descent, but ends up lying outside the calibrated bed.
Logic adapted from the pose_app prototype (DetectorCaidas.kt), measured in
torso lengths like fall.py so it does not depend on the distance to the camera.

Calibrate locally: python -m edge.bed --camera 0 --out edge/models/cama.json
The polygon never leaves this computer and no image is written.
"""

import argparse
import dataclasses
import json
import math
from collections import deque
from pathlib import Path

from . import options

SHOULDERS, HIPS, HEAD = (11, 12), (23, 24), (0, 7, 8)
MIN_AREA = 0.001  # fraction of the frame; smaller means a mis-click, not a bed
BORDER = 1e-4


class BedZone:
    """Polygon in normalized image coordinates; the border counts as inside."""

    def __init__(self, points):
        if not isinstance(points, list) or not 3 <= len(points) <= 8:
            raise ValueError("La zona de cama necesita de 3 a 8 vértices.")
        checked = []
        for p in points:
            if (
                not isinstance(p, (list, tuple))
                or len(p) != 2
                or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in p)
                or not all(math.isfinite(v) and 0 <= v <= 1 for v in p)
            ):
                raise ValueError("Cada vértice es [x, y] con valores entre 0 y 1.")
            checked.append((float(p[0]), float(p[1])))
        # Corners clicked in any order must not make a crossed polygon.
        cx = sum(x for x, _ in checked) / len(checked)
        cy = sum(y for _, y in checked) / len(checked)
        self.points = sorted(checked, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
        if self.area() < MIN_AREA:
            raise ValueError("La zona de cama es demasiado pequeña.")

    @classmethod
    def from_file(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data) != {"bed"}:
            raise ValueError('El archivo de cama debe tener solo la clave "bed".')
        return cls(data["bed"])

    def to_json(self):
        return {"bed": [[round(x, 4), round(y, 4)] for x, y in self.points]}

    def area(self):
        pts = self.points
        return abs(sum(
            pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts))
        )) / 2

    def contains(self, x, y):
        pts = self.points
        for i in range(len(pts)):
            if _on_segment((x, y), pts[i - 1], pts[i]):
                return True
        inside = False
        for i in range(len(pts)):
            (ax, ay), (bx, by) = pts[i], pts[i - 1]
            if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                inside = not inside
        return inside


def _on_segment(p, a, b):
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    return (
        abs(cross) <= BORDER
        and min(a[0], b[0]) - BORDER <= p[0] <= max(a[0], b[0]) + BORDER
        and min(a[1], b[1]) - BORDER <= p[1] <= max(a[1], b[1]) + BORDER
    )


@dataclasses.dataclass(frozen=True)
class BedConfig:
    lying_angle: float = 60.0
    lying_seconds: float = 5.0
    smoothing_frames: int = 8
    track_gap_seconds: float = 1.5
    # Torso lengths per second; a faster jump means MediaPipe switched to
    # something else (a sheet on the floor). To be tuned with the protocol.
    max_track_speed: float = 8.0
    rearm_upright_seconds: float = 3.0
    min_visibility: float = 0.5

    def __post_init__(self):
        options.check_positive(self)
        if self.lying_angle > 90 or self.min_visibility > 1:
            raise ValueError("lying_angle va hasta 90 y min_visibility hasta 1.")


def add_arguments(parser):
    group = options.add_arguments(
        parser, BedConfig, "bed", "zona de cama (spec 017)", "JSON local con umbrales de cama"
    )
    group.add_argument("--bed-config", help="JSON local con la zona de cama (python -m edge.bed)")


def config_from_args(args):
    return options.config_from_args(args, BedConfig, "bed", "cama")


@dataclasses.dataclass(frozen=True)
class Body:
    point: tuple  # normalized (x, y) used for inside/outside
    kind: str  # "hips", "shoulders" or "head"
    angle: float | None  # trunk from vertical, degrees; None with one point only
    torso: float | None  # shoulders-hips length in image heights


def body_reference(landmarks, frame_aspect=1.0, min_visibility=0.5):
    """Reference point with fallbacks hips -> shoulders -> head (covered person)."""
    if len(landmarks) != 33:
        return None

    def visible(i):
        p = landmarks[i]
        return min(p.get("visibility", 0), p.get("presence", 0)) >= min_visibility and all(
            math.isfinite(float(p.get(k, math.nan))) for k in ("x", "y")
        )

    def mean(indexes):
        seen = [landmarks[i] for i in indexes if visible(i)]
        if not seen:
            return None
        return (sum(p["x"] for p in seen) / len(seen), sum(p["y"] for p in seen) / len(seen))

    hips, shoulders, head = mean(HIPS), mean(SHOULDERS), mean(HEAD)
    found = [(p, k) for p, k in ((hips, "hips"), (shoulders, "shoulders"), (head, "head")) if p]
    if not found:
        return None
    pair = next(
        ((top, bottom) for top, bottom in ((shoulders, hips), (head, hips), (head, shoulders))
         if top and bottom),
        None,
    )
    angle = torso = None
    if pair:
        dx, dy = (pair[0][0] - pair[1][0]) * frame_aspect, pair[0][1] - pair[1][1]
        angle = math.degrees(math.atan2(abs(dx), abs(dy)))
    if shoulders and hips:
        torso = math.hypot((shoulders[0] - hips[0]) * frame_aspect, shoulders[1] - hips[1])
    return Body(found[0][0], found[0][1], angle, torso)


class BedFallRule:
    """Outside the bed and lying for `lying_seconds`, followed without jumps.

    observe() returns "fall" once per event, "no_person" when the frame has no
    usable person (also a sudden "lying" shape on the floor: likely a sheet) or "".
    """

    def __init__(self, zone, config=None, frame_aspect=1.0):
        if not math.isfinite(frame_aspect) or frame_aspect <= 0:
            raise ValueError("La relación de aspecto del cuadro debe ser positiva.")
        self.zone, self.config, self.frame_aspect = zone, config or BedConfig(), frame_aspect
        self.reset()

    def reset(self):
        self.outside = deque(maxlen=self.config.smoothing_frames)
        self.last, self.last_time, self.scale = None, None, None
        # True once, in this track, the person was seen in bed or not lying.
        self.valid_track = False
        self.in_bed, self.alerted = False, False
        self.lying_since, self.upright_since = None, None

    def rearmed(self, now):
        """Back in bed, or seen not lying for rearm_upright_seconds in a row."""
        return self.in_bed or (
            self.upright_since is not None
            and now - self.upright_since >= self.config.rearm_upright_seconds
        )

    def observe(self, landmarks, now):
        c = self.config
        b = body_reference(landmarks, self.frame_aspect, c.min_visibility)
        if b is None:
            return self._no_person()
        if b.torso:
            self.scale = b.torso
        if self._jumped(b, now):
            self.valid_track, self.lying_since = False, None
        self.last, self.last_time = b, now

        outside_raw = not self.zone.contains(*b.point)
        lying = None if b.angle is None else b.angle >= c.lying_angle
        if not outside_raw or lying is False:
            self.valid_track = True
        if outside_raw and lying and not self.valid_track:
            return self._no_person()
        self.outside.append(outside_raw)
        outside = sum(self.outside) > len(self.outside) / 2
        if outside and lying is None:
            return self._no_person()  # one point outside: posture unknown

        if not outside:
            self.in_bed, self.alerted = True, False
            self.lying_since = self.upright_since = None
            return ""
        self.in_bed = False
        if lying:
            self.upright_since = None
            if self.lying_since is None:
                self.lying_since = now
            if now - self.lying_since >= c.lying_seconds and not self.alerted:
                self.alerted = True
                return "fall"
            return ""
        self.lying_since = None
        if self.upright_since is None:
            self.upright_since = now
        if self.rearmed(now):
            self.alerted = False
        return ""

    def _jumped(self, b, now):
        if self.last is None or now - self.last_time > self.config.track_gap_seconds:
            return True
        dt = now - self.last_time
        if b.kind != self.last.kind or dt <= 0 or not self.scale:
            return False  # a switched reference point is not a real movement
        dx = (b.point[0] - self.last.point[0]) * self.frame_aspect
        speed = math.hypot(dx, b.point[1] - self.last.point[1]) / self.scale / dt
        return speed > self.config.max_track_speed

    def _no_person(self):
        self.upright_since = None  # "upright" must be seen without gaps
        return "no_person"


def calibrate(camera, out):
    """Click the bed corners on the live image; Enter saves, r restarts, Esc cancels."""
    import cv2
    import numpy as np

    source = int(camera) if camera.isdigit() else camera
    capture = cv2.VideoCapture(source)
    points, window = [], "VIGIA: marca las esquinas de la cama"
    size = [1, 1]

    def click(event, x, y, *_):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 8:
            points.append([x / size[0], y / size[1]])

    cv2.namedWindow(window)
    cv2.setMouseCallback(window, click)
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                raise SystemExit("Sin imagen de cámara.")
            size[:] = frame.shape[1], frame.shape[0]
            pixels = [(int(x * size[0]), int(y * size[1])) for x, y in points]
            for p in pixels:
                cv2.circle(frame, p, 6, (0, 200, 255), -1)
            if len(pixels) > 1:
                cv2.polylines(frame, [np.array(pixels, np.int32)], True, (0, 200, 255), 2)
            cv2.imshow(window, frame)
            key = cv2.waitKey(30) & 0xFF
            if key == 27:
                raise SystemExit("Calibración cancelada; no se guardó nada.")
            if key == ord("r"):
                points.clear()
            if key in (10, 13) and len(points) >= 3:
                try:
                    zone = BedZone(points)
                except ValueError as exc:
                    print(f"{exc} Vuelve a marcar (r).")
                    continue
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                Path(out).write_text(json.dumps(zone.to_json(), indent=2), encoding="utf-8")
                print(f"Zona de cama guardada en {out} (solo coordenadas, sin imágenes).")
                return zone
    finally:
        capture.release()
        cv2.destroyAllWindows()


def main():
    p = argparse.ArgumentParser(description="Calibración local de la zona de cama")
    p.add_argument("--camera", default="0", help="Índice de cámara o video local")
    p.add_argument("--out", default="edge/models/cama.json")
    a = p.parse_args()
    calibrate(a.camera, a.out)


if __name__ == "__main__":
    main()
