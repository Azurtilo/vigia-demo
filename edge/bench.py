"""Offline benchmark: python -m edge.bench video.mp4 [...]. No server, no upload.

Uses the video's own timestamps, so the fall rule sees real time even when
inference is slower or faster than the recording.
"""

import argparse
import json
import time

from .fall import FallDetector, add_arguments, config_from_args
from .metrics import LatencyStats
from .run import DEFAULT_MODEL, as_dicts


def args_parser():
    p = argparse.ArgumentParser(
        description="Latencia, FPS y caídas detectadas en videos locales autorizados"
    )
    p.add_argument("videos", nargs="+", help="Videos locales (uno por prueba)")
    p.add_argument("--model", default=str(DEFAULT_MODEL))
    p.add_argument("--json", action="store_true", help="Salida JSON")
    add_arguments(p)
    return p


def bench_video(path, model, config):
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    capture = cv2.VideoCapture(path)
    if not capture.isOpened():
        raise SystemExit(f"No se pudo abrir el video: {path}")
    video_fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=model),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=2,
        min_pose_detection_confidence=0.7,
        min_pose_presence_confidence=0.7,
        min_tracking_confidence=0.7,
    )
    stats, events, fall = LatencyStats(), [], None
    frames = with_person = 0
    started = time.perf_counter()
    # A fresh landmarker per video: VIDEO mode needs increasing timestamps.
    with vision.PoseLandmarker.create_from_options(options) as detector:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            now = frames / video_fps
            frames += 1
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            t0 = time.perf_counter()
            result = detector.detect_for_video(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), int(now * 1000)
            )
            stats.add((time.perf_counter() - t0) * 1000)
            landmarks = []
            if len(result.pose_landmarks) == 1:
                with_person += 1
                landmarks = as_dicts(result.pose_landmarks[0])
            if fall is None:
                fall = FallDetector(config, frame.shape[1] / frame.shape[0])
            if fall.observe(landmarks, now) == "fall":
                events.append(
                    {"impact_s": round(fall.impact_at, 2), "confirmed_s": round(now, 2)}
                )
    capture.release()
    elapsed = time.perf_counter() - started
    return {
        "video": str(path),
        "frames": frames,
        "frames_with_one_person": with_person,
        "video_seconds": round(frames / video_fps, 2),
        "inference": stats.summary(),
        "processing_fps": round(frames / elapsed, 2) if elapsed else None,
        "falls": len(events),
        "events": events,
    }


def main():
    a = args_parser().parse_args()
    try:
        config = config_from_args(a)
    except (OSError, ValueError, TypeError) as exc:
        raise SystemExit(f"Configuración de caídas inválida: {exc}")
    reports = [bench_video(v, a.model, config) for v in a.videos]
    totals = {
        "videos": len(reports),
        "videos_with_fall": sum(1 for r in reports if r["falls"]),
        "falls": sum(r["falls"] for r in reports),
    }
    if a.json:
        print(json.dumps({"config": vars(config), "reports": reports, "totals": totals}, indent=2))
        return
    for r in reports:
        inf = r["inference"] or {"mean_ms": 0, "p95_ms": 0, "max_ms": 0}
        print(
            f"{r['video']}: {r['frames']} cuadros ({r['video_seconds']} s), "
            f"persona única en {r['frames_with_one_person']}; inferencia promedio "
            f"{inf['mean_ms']} ms, p95 {inf['p95_ms']} ms, máx {inf['max_ms']} ms; "
            f"{r['processing_fps']} FPS; caídas {r['falls']} {r['events']}"
        )
    print(
        f"Total: {totals['videos']} videos, {totals['videos_with_fall']} con caída, "
        f"{totals['falls']} caídas detectadas."
    )


if __name__ == "__main__":
    main()
