"""Local MediaPipe processor: python -m edge.run --help. No frame upload."""

import argparse
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

from .fall import FallDetector, add_arguments, config_from_args
from .metrics import LatencyStats
from .posture import CalibratedClassifier, ImmobilityRule, features

DEFAULT_MODEL = Path(__file__).resolve().parent / "models" / "pose_landmarker_lite.task"
# The server rejects observations older than 2 minutes; stop retrying before that.
FALL_RETRY_SECONDS = 110
log = logging.getLogger("vigia.edge")


def args_parser():
    p = argparse.ArgumentParser(
        description="Nodo local VIGIA con calibración de postura"
    )
    p.add_argument(
        "--model",
        default=str(DEFAULT_MODEL),
        help="Modelo local pose_landmarker.task (por defecto edge/models/)",
    )
    p.add_argument("--references", required=True, help="JSON local de calibración")
    p.add_argument(
        "--camera", default="0", help="Índice de cámara o video de prueba local"
    )
    p.add_argument("--server", default="http://127.0.0.1:8000")
    p.add_argument(
        "--calibrate", choices=["supina", "lateral-izquierda", "lateral-derecha"]
    )
    p.add_argument("--immobility-minutes", type=int, choices=[60, 90, 120], default=120)
    p.add_argument("--allow-local-http", action="store_true")
    p.add_argument("--log-file", help="Archivo local adicional para el log")
    p.add_argument(
        "--metrics-seconds",
        type=float,
        default=60,
        help="Intervalo del resumen de inferencia en el log (por defecto 60 s)",
    )
    add_arguments(p)
    return p


def setup_logging(log_file=None):
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
    )


def as_dicts(points):
    return [
        {
            "x": p.x,
            "y": p.y,
            "z": p.z,
            "visibility": p.visibility,
            "presence": p.presence,
        }
        for p in points
    ]


def main():
    a = args_parser().parse_args()
    setup_logging(a.log_file)
    try:
        fall_config = config_from_args(a)
    except (OSError, ValueError, TypeError) as exc:
        raise SystemExit(f"Configuración de caídas inválida: {exc}")
    import cv2
    import mediapipe as mp
    import requests
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    host = urlparse(a.server)
    if (
        not a.calibrate
        and host.scheme != "https"
        and not (a.allow_local_http and host.hostname in ("127.0.0.1", "localhost"))
    ):
        raise SystemExit("Usa HTTPS o --allow-local-http exclusivamente para loopback.")
    token = os.environ.get("VIGIA_NODE_TOKEN", "")
    if not a.calibrate and not token:
        raise SystemExit(
            "Configura VIGIA_NODE_TOKEN fuera de los archivos del proyecto."
        )
    reference_path = Path(a.references)
    references = (
        json.loads(reference_path.read_text()) if reference_path.exists() else {}
    )
    classifier = None if a.calibrate else CalibratedClassifier(references)
    rule = ImmobilityRule(a.immobility_minutes * 60)
    fall = None  # created on the first frame, when its aspect ratio is known
    source = int(a.camera) if a.camera.isdigit() else a.camera
    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=a.model),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=2,
        min_pose_detection_confidence=0.7,
        min_pose_presence_confidence=0.7,
        min_tracking_confidence=0.7,
    )
    samples, lease_until, sent_at, last_posture = [], 0.0, 0.0, None
    stats, metrics_since = LatencyStats(), time.monotonic()
    pending_falls = []  # (monotonic created, payload); same event_id on retry
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = a.server.rstrip("/") + "/api/v1/edge/observations"
    capture = None
    try:
        with vision.PoseLandmarker.create_from_options(options) as detector:
            while True:
                now = time.monotonic()
                if not a.calibrate and now >= lease_until:
                    try:
                        response = requests.get(
                            a.server.rstrip("/") + "/api/v1/edge/status",
                            headers=headers,
                            timeout=5,
                        )
                        response.raise_for_status()
                        lease_until = now + min(15, response.json()["lease_seconds"])
                    except (requests.RequestException, ValueError, KeyError):
                        if capture:
                            capture.release()
                            capture = None
                        classifier = CalibratedClassifier(references)
                        rule = ImmobilityRule(a.immobility_minutes * 60)
                        fall = None
                        log.warning(
                            "Monitoreo detenido: sin permiso o conexión al servidor."
                        )
                        time.sleep(5)
                        continue
                if capture is None:
                    capture = cv2.VideoCapture(source)
                ok, frame = capture.read()
                if not ok:
                    log.warning("Sin imagen de cámara. No se infiere inmovilidad.")
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                started = time.perf_counter()
                result = detector.detect_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb),
                    int(now * 1000),
                )
                stats.add((time.perf_counter() - started) * 1000)
                if now - metrics_since >= a.metrics_seconds:
                    summary = stats.summary()
                    if summary:
                        log.info(
                            "Inferencia: cuadros=%d promedio=%.1f ms p95=%.1f ms máx=%.1f ms fps=%.1f",
                            summary["frames"],
                            summary["mean_ms"],
                            summary["p95_ms"],
                            summary["max_ms"],
                            summary["frames"] / (now - metrics_since),
                        )
                    stats.reset()
                    metrics_since = now
                landmarks, image_landmarks = [], []
                # Only one person in view; two people make geometry ambiguous.
                if len(result.pose_world_landmarks) == 1:
                    landmarks = as_dicts(result.pose_world_landmarks[0])
                    image_landmarks = as_dicts(result.pose_landmarks[0])
                if a.calibrate:
                    f = features(landmarks)
                    if f is not None:
                        samples.append(f)
                    else:
                        samples.clear()
                    log.info(
                        "Calibración %s: %d/60 muestras válidas", a.calibrate, len(samples)
                    )
                    if len(samples) >= 60:
                        references[a.calibrate] = [
                            sum(row[i] for row in samples) / len(samples)
                            for i in range(24)
                        ]
                        reference_path.parent.mkdir(parents=True, exist_ok=True)
                        reference_path.write_text(json.dumps(references, indent=2))
                        log.info("Referencia guardada localmente, sin imágenes.")
                        break
                    continue
                if fall is None:
                    fall = FallDetector(fall_config, frame.shape[1] / frame.shape[0])
                posture, confidence = classifier.classify(landmarks, now)
                risk = rule.observe(posture, now)
                if fall.observe(image_landmarks, now) == "fall":
                    confirmed = datetime.now(timezone.utc)
                    impact = confirmed - timedelta(seconds=now - fall.impact_at)
                    payload = {
                        "event_id": str(uuid.uuid4()),
                        "observed_at": confirmed.isoformat(),
                        "posture": posture,
                        "confidence": confidence,
                        "model_version": "mediapipe-pose-landmarker-local",
                        "rule_version": "fall-v1",
                        "risk": "fall",
                    }
                    pending_falls.append((now, payload))
                    log.warning(
                        "Caída confirmada: event_id=%s impacto=%s confirmada=%s confirmación=%.2f s",
                        payload["event_id"],
                        impact.isoformat(),
                        confirmed.isoformat(),
                        now - fall.impact_at,
                    )
                for item in list(pending_falls):
                    created, payload = item
                    if now - created > FALL_RETRY_SECONDS:
                        pending_falls.remove(item)
                        log.error(
                            "Caída no entregada al servidor: event_id=%s", payload["event_id"]
                        )
                        continue
                    try:
                        response = requests.post(
                            endpoint, headers=headers, json=payload, timeout=5
                        )
                        response.raise_for_status()
                        pending_falls.remove(item)
                        log.warning(
                            "Caída enviada: event_id=%s envío=%s retraso=%.2f s",
                            payload["event_id"],
                            datetime.now(timezone.utc).isoformat(),
                            time.monotonic() - created,
                        )
                    except requests.RequestException:
                        lease_until = 0  # fail closed; keep the fall for retry
                        break
                if posture != last_posture or risk or now - sent_at >= 30:
                    payload = {
                        "event_id": str(uuid.uuid4()),
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                        "posture": posture,
                        "confidence": confidence,
                        "model_version": "mediapipe-pose-landmarker-local",
                        "rule_version": "calibrated-v1",
                        "risk": risk,
                    }
                    try:
                        response = requests.post(
                            endpoint, headers=headers, json=payload, timeout=5
                        )
                        response.raise_for_status()
                        sent_at, last_posture = now, posture
                        log.info("Observación enviada: %s", posture)
                    except requests.RequestException:
                        lease_until = 0  # fail closed on transmission failure
                time.sleep(0.05)
    finally:
        if capture:
            capture.release()


if __name__ == "__main__":
    main()
