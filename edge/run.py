"""Local MediaPipe processor: python -m edge.run --help. No frame upload."""

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .posture import CalibratedClassifier, ImmobilityRule, features


def args_parser():
    p = argparse.ArgumentParser(
        description="Nodo local VIGIA con calibración de postura"
    )
    p.add_argument("--model", required=True, help="Modelo local pose_landmarker.task")
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
    return p


def main():
    a = args_parser().parse_args()
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
    headers = {"Authorization": f"Bearer {token}"}
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
                        print(
                            "Monitoreo detenido: sin permiso o conexión al servidor.",
                            flush=True,
                        )
                        time.sleep(5)
                        continue
                if capture is None:
                    capture = cv2.VideoCapture(source)
                ok, frame = capture.read()
                if not ok:
                    print(
                        "Sin imagen de cámara. No se infiere inmovilidad.", flush=True
                    )
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = detector.detect_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb),
                    int(now * 1000),
                )
                landmarks = []
                if len(result.pose_world_landmarks) == 1:
                    landmarks = [
                        {
                            "x": p.x,
                            "y": p.y,
                            "z": p.z,
                            "visibility": p.visibility,
                            "presence": p.presence,
                        }
                        for p in result.pose_world_landmarks[0]
                    ]
                if a.calibrate:
                    f = features(landmarks)
                    if f is not None:
                        samples.append(f)
                    else:
                        samples.clear()
                    print(
                        f"Calibración {a.calibrate}: {len(samples)}/60 muestras válidas",
                        flush=True,
                    )
                    if len(samples) >= 60:
                        references[a.calibrate] = [
                            sum(row[i] for row in samples) / len(samples)
                            for i in range(24)
                        ]
                        reference_path.parent.mkdir(parents=True, exist_ok=True)
                        reference_path.write_text(json.dumps(references, indent=2))
                        print(
                            "Referencia guardada localmente, sin imágenes.", flush=True
                        )
                        break
                    continue
                posture, confidence = classifier.classify(landmarks, now)
                risk = rule.observe(posture, now)
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
                            a.server.rstrip("/") + "/api/v1/edge/observations",
                            headers=headers,
                            json=payload,
                            timeout=5,
                        )
                        response.raise_for_status()
                        sent_at, last_posture = now, posture
                        print(f"Observación enviada: {posture}", flush=True)
                    except requests.RequestException:
                        lease_until = 0  # fail closed on transmission failure
                time.sleep(0.05)
    finally:
        if capture:
            capture.release()


if __name__ == "__main__":
    main()
