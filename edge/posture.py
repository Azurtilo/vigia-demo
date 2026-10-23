"""Calibrated geometric classifier. No clinical claims or built-in pose labels."""

import math

LABELS = ("supina", "lateral-izquierda", "lateral-derecha")
BODY = (11, 12, 23, 24, 25, 26, 27, 28)


def features(landmarks, min_visibility=0.7):
    if len(landmarks) != 33:
        return None
    points = [landmarks[i] for i in BODY]
    if any(
        min(p.get("visibility", 0), p.get("presence", 0)) < min_visibility
        for p in points
    ):
        return None
    if any(not math.isfinite(float(p[k])) for p in points for k in ("x", "y", "z")):
        return None
    center = [(points[2][k] + points[3][k]) / 2 for k in ("x", "y", "z")]
    shoulder = [(points[0][k] + points[1][k]) / 2 for k in ("x", "y", "z")]
    scale = math.dist(center, shoulder)
    if scale < 0.05:
        return None
    return [
        (p[k] - center[j]) / scale
        for p in points
        for j, k in enumerate(("x", "y", "z"))
    ]


class CalibratedClassifier:
    def __init__(self, references, max_distance=0.35, margin=0.08, stable_seconds=3):
        if set(references) != set(LABELS) or any(
            len(v) != 24 or not all(math.isfinite(float(x)) for x in v)
            for v in references.values()
        ):
            raise ValueError(
                "Calibra las tres posturas con 24 valores finitos por referencia."
            )
        self.references = references
        self.max_distance, self.margin, self.stable_seconds = (
            max_distance,
            margin,
            stable_seconds,
        )
        self.candidate, self.since, self.last_time = None, None, None

    def classify(self, landmarks, now):
        f = features(landmarks)
        # A gap resets evidence. A disconnected camera cannot imply stability.
        if self.last_time is not None and now - self.last_time > 2:
            self.candidate, self.since = None, None
        self.last_time = now
        if f is None:
            self.candidate, self.since = None, None
            return "indeterminada", 0.0
        distances = sorted(
            (math.dist(f, ref) / math.sqrt(len(f)), label)
            for label, ref in self.references.items()
        )
        best, label = distances[0]
        if best > self.max_distance or distances[1][0] - best < self.margin:
            self.candidate, self.since = None, None
            return "indeterminada", 0.0
        if label != self.candidate:
            self.candidate, self.since = label, now
        if now - self.since < self.stable_seconds:
            return "indeterminada", 0.0
        # Similarity is an engineering score, not a calibrated clinical probability.
        return label, round(max(0, 1 - best / self.max_distance), 4)


class ImmobilityRule:
    def __init__(self, seconds):
        if seconds < 60:
            raise ValueError("El intervalo debe ser de al menos 60 segundos.")
        self.seconds, self.label, self.since, self.last_time, self.emitted = (
            seconds,
            None,
            None,
            None,
            False,
        )

    def observe(self, label, now):
        if label == "indeterminada" or (
            self.last_time is not None and now - self.last_time > 2
        ):
            self.label, self.since, self.emitted = None, None, False
        self.last_time = now
        if label == "indeterminada":
            return ""
        if label != self.label:
            self.label, self.since, self.emitted = label, now, False
        if now - self.since >= self.seconds and not self.emitted:
            self.emitted = True
            return "immobility"
        return ""
