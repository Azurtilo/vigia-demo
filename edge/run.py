"""Local MediaPipe processor: python -m edge.run --help. No frame upload."""

import argparse
import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

from . import bed, monitoring
from .fall import FallDetector, add_arguments, config_from_args
from .metrics import LatencyStats
from .posture import CalibratedClassifier, ImmobilityRule, features

DEFAULT_MODEL = Path(__file__).resolve().parent / "models" / "pose_landmarker_lite.task"
# The server accepts ordinary observations up to 2 minutes old and risk events
# (fall, immobility) up to 1 hour; stop retrying before each limit.
OBSERVATION_RETRY_SECONDS = 110
RISK_RETRY_SECONDS = 55 * 60
LEASE_SECONDS = 15  # local cap of the server lease
LEASE_REFRESH_SECONDS = 10  # renew before it expires
MAX_BACKOFF_SECONDS = 30
MAX_PENDING = 500
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
    bed.add_arguments(p)
    monitoring.add_arguments(p)
    return p


def bed_from_args(a):
    """(zone or None, BedConfig); exits with a clear message when invalid."""
    try:
        zone = bed.BedZone.from_file(a.bed_config) if a.bed_config else None
        return zone, bed.config_from_args(a)
    except (OSError, ValueError, TypeError) as exc:
        raise SystemExit(f"Configuración de cama inválida: {exc}")


def monitor_config_from_args(a):
    try:
        return monitoring.config_from_args(a)
    except (OSError, ValueError, TypeError) as exc:
        raise SystemExit(f"Configuración del estado de monitoreo inválida: {exc}")


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


class Uplink:
    """Lease and delivery in a worker thread: network delays never block frames.

    Pending observations keep their original event_id and observed_at, so a
    retry after a timeout is deduplicated by the server. The lease is the only
    signal the frame loop reads; it fails closed when it expires or is denied.
    Each renewal also reports the monitoring state (spec 017, D-073); a server
    without that support ignores the parameter.
    """

    def __init__(self, server, token, session=None, clock=time.monotonic):
        if session is None:
            import requests as session
        self.session, self.clock = session, clock
        self.status_url = server.rstrip("/") + "/api/v1/edge/status"
        self.endpoint = server.rstrip("/") + "/api/v1/edge/observations"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.pending = []  # [monotonic created, payload]
        self.lease_until, self.next_lease = 0.0, 0.0
        self.failures, self.retry_at = 0, 0.0
        self.monitor_state = monitoring.NORMAL
        self.lock, self.wake, self.stopped = (
            threading.Lock(),
            threading.Event(),
            threading.Event(),
        )
        self.thread = None

    def lease_active(self, now):
        return now < self.lease_until

    def set_monitor_state(self, state):
        """A change is reported at once instead of waiting for the next renewal."""
        if state not in monitoring.STATES:
            raise ValueError(f"Estado de monitoreo desconocido: {state}")
        with self.lock:
            if state == self.monitor_state:
                return
            self.monitor_state, self.next_lease = state, 0.0
        self.wake.set()

    def enqueue(self, payload):
        with self.lock:
            self.pending.append((self.clock(), payload))
            if len(self.pending) > MAX_PENDING:
                ordinary = [i for i in self.pending if not i[1]["risk"]]
                self.pending.remove(ordinary[0] if ordinary else self.pending[0])
        self.wake.set()

    def step(self):
        """One worker iteration; returns the seconds to wait before the next."""
        now = self.clock()
        if now < self.retry_at:
            return self.retry_at - now
        if now >= self.next_lease and not self._renew(now):
            return self.retry_at - now
        item = self._next(now)
        if item is None:
            return max(0.05, self.next_lease - now)
        self._deliver(item, now)
        return 0.0 if self.failures == 0 else self.retry_at - now

    def _next(self, now):
        with self.lock:
            for item in list(self.pending):
                created, payload = item
                limit = RISK_RETRY_SECONDS if payload["risk"] else OBSERVATION_RETRY_SECONDS
                if now - created > limit:
                    self.pending.remove(item)
                    (log.error if payload["risk"] else log.info)(
                        "Observación no entregada al servidor: riesgo=%s event_id=%s",
                        payload["risk"] or "-",
                        payload["event_id"],
                    )
            # Risk events first, each group in arrival order.
            return min(
                self.pending, key=lambda i: (not i[1]["risk"], i[0]), default=None
            )

    def _renew(self, now):
        try:
            response = self.session.get(
                self.status_url,
                headers=self.headers,
                params={"monitor_state": self.monitor_state},
                timeout=5,
            )
            if response.status_code in (401, 403):
                self.lease_until = 0.0  # explicit denial stops capture at once
            response.raise_for_status()
            seconds = min(LEASE_SECONDS, float(response.json()["lease_seconds"]))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            # requests exceptions derive from OSError.
            return self._failed(now, f"autorización: {type(exc).__name__}")
        # Measured from the request start, so a slow answer shortens the lease.
        self.lease_until, self.next_lease = now + seconds, now + LEASE_REFRESH_SECONDS
        return True

    def _deliver(self, item, now):
        created, payload = item
        try:
            response = self.session.post(
                self.endpoint, headers=self.headers, json=payload, timeout=5
            )
        except OSError as exc:
            self._failed(now, f"envío: {type(exc).__name__}")
            return
        status = response.status_code
        if status in (401, 403):
            self.lease_until = 0.0
            self._failed(now, f"envío rechazado: HTTP {status}")
            return
        if status in (400, 409, 413):
            # Permanent: the server will never accept this payload.
            self._drop(item)
            log.error("Observación descartada por el servidor: HTTP %d event_id=%s",
                      status, payload["event_id"])
            return
        if status >= 300:
            self._failed(now, f"envío: HTTP {status}")
            return
        self._drop(item)
        self.failures, self.retry_at = 0, 0.0
        if payload["risk"]:
            log.warning(
                "Riesgo %s enviado: event_id=%s envío=%s retraso=%.2f s",
                payload["risk"],
                payload["event_id"],
                datetime.now(timezone.utc).isoformat(),
                self.clock() - created,
            )
        else:
            log.info("Observación enviada: %s", payload["posture"])

    def _drop(self, item):
        with self.lock:
            if item in self.pending:  # enqueue may have evicted it meanwhile
                self.pending.remove(item)

    def _failed(self, now, reason):
        self.failures += 1
        delay = min(MAX_BACKOFF_SECONDS, 2 ** (self.failures - 1))
        self.retry_at = now + delay
        log.warning("Servidor no disponible (%s); reintento en %d s, pendientes=%d",
                    reason, delay, len(self.pending))
        return False

    def run(self):
        while not self.stopped.is_set():
            self.wake.clear()
            try:
                delay = self.step()
            except Exception:  # keep the worker alive; the lease still fails closed
                log.exception("Error inesperado en el envío.")
                self._failed(self.clock(), "error interno")
                delay = 1.0
            self.wake.wait(min(1.0, max(0.0, delay)))

    def start(self):
        self.thread = threading.Thread(target=self.run, name="vigia-uplink", daemon=True)
        self.thread.start()

    def stop(self, drain_seconds=5.0):
        """Give pending events a short chance to leave, then stop the worker."""
        deadline = time.monotonic() + drain_seconds
        while self.pending and time.monotonic() < deadline:
            time.sleep(0.1)
        self.stopped.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=6)


class Monitor:
    """Per-frame rules. Never touches the network: payloads go to the uplink.

    With a bed zone (spec 017) a second fall rule runs beside the impact rule;
    a shared latch sends one fall per event until the person is back in bed or
    upright again. Without a bed zone the behaviour is that of spec 012.
    The monitoring state (spec 017) says when the camera cannot really watch.
    """

    def __init__(self, references, immobility_seconds, fall_config, uplink,
                 wall_clock=lambda: datetime.now(timezone.utc),
                 bed_zone=None, bed_config=None, monitor_config=None):
        self.references, self.immobility_seconds = references, immobility_seconds
        self.fall_config, self.uplink, self.wall_clock = fall_config, uplink, wall_clock
        self.bed_zone, self.bed_config = bed_zone, bed_config
        self.status = monitoring.MonitorStatus(monitor_config)
        self.reset()

    def reset(self):
        self.classifier = CalibratedClassifier(self.references)
        self.rule = ImmobilityRule(self.immobility_seconds)
        self.fall = None  # created on the first frame, when its aspect ratio is known
        self.bed, self.bed_result, self.fall_latched = None, "", False
        self.last_posture, self.sent_at = None, None
        # A lease pause is a deliberate stop, not a blind camera: start over.
        self.status.reset()
        if self.uplink:
            self.uplink.set_monitor_state(monitoring.NORMAL)

    def tick(self, now):
        """No frame this time (camera lost); keeps the monitoring state current."""
        self.state_changed(self.status.tick(now))

    def state_changed(self, state):
        if state is None:
            return
        (log.info if state == monitoring.NORMAL else log.warning)(
            "Estado de monitoreo: %s", state
        )
        self.uplink.set_monitor_state(state)

    def send_fall(self, rule_version, started, posture, confidence, now):
        confirmed = self.wall_clock()
        payload = self.payload(confirmed, posture, confidence, rule_version, "fall")
        self.uplink.enqueue(payload)
        # Impact for fall-v1; start of "lying outside the bed" for fall-bed-v1.
        log.warning(
            "Caída confirmada (%s): event_id=%s inicio=%s confirmada=%s confirmación=%.2f s",
            rule_version,
            payload["event_id"],
            (confirmed - timedelta(seconds=now - started)).isoformat(),
            confirmed.isoformat(),
            now - started,
        )

    def payload(self, observed, posture, confidence, rule_version, risk):
        return {
            "event_id": str(uuid.uuid4()),
            "observed_at": observed.isoformat(),
            "posture": posture,
            "confidence": confidence,
            "model_version": "mediapipe-pose-landmarker-local",
            "rule_version": rule_version,
            "risk": risk,
        }

    def process(self, landmarks, image_landmarks, now, frame_aspect,
                brightness=None, people=None):
        """`people`: persons detected (the rules only run with exactly one)."""
        if self.fall is None:
            self.fall = FallDetector(self.fall_config, frame_aspect)
            if self.bed_zone:
                self.bed = bed.BedFallRule(self.bed_zone, self.bed_config, frame_aspect)
        posture, confidence = self.classifier.classify(landmarks, now)
        risk = self.rule.observe(posture, now)
        impact = self.fall.observe(image_landmarks, now) == "fall"
        self.bed_result = self.bed.observe(image_landmarks, now) if self.bed else ""
        if self.fall_latched and self.bed.rearmed(now):
            self.fall_latched = False
        for rule_version, started, emitted in (
            ("fall-v1", self.fall.impact_at, impact),
            ("fall-bed-v1", self.bed and self.bed.lying_since, self.bed_result == "fall"),
        ):
            if not emitted:
                continue
            if self.fall_latched:
                log.info("Caída ya avisada para este evento (%s).", rule_version)
                continue
            self.fall_latched = self.bed is not None
            self.send_fall(rule_version, started, posture, confidence, now)
        if people is None:
            people = 1 if image_landmarks else 0
        if self.bed:
            usable = self.bed_result != "no_person"
        else:
            usable = bed.body_reference(image_landmarks, frame_aspect) is not None
        # Two people in view: someone is there (often the caregiver), not "lost".
        self.state_changed(self.status.frame(now, people >= 2 or usable, brightness))
        if (
            posture != self.last_posture
            or risk
            or self.sent_at is None
            or now - self.sent_at >= 30
        ):
            self.uplink.enqueue(
                self.payload(self.wall_clock(), posture, confidence, "calibrated-v1", risk)
            )
            self.sent_at, self.last_posture = now, posture
        return posture, risk


def check_server(a, token):
    host = urlparse(a.server)
    if (
        not a.calibrate
        and host.scheme != "https"
        and not (a.allow_local_http and host.hostname in ("127.0.0.1", "localhost"))
    ):
        raise SystemExit("Usa HTTPS o --allow-local-http exclusivamente para loopback.")
    if not a.calibrate and not token:
        raise SystemExit(
            "Configura VIGIA_NODE_TOKEN fuera de los archivos del proyecto."
        )


def calibration_step(samples, landmarks, name, references, reference_path):
    """Adds one sample; True once the reference is saved locally."""
    f = features(landmarks)
    if f is not None:
        samples.append(f)
    else:
        samples.clear()
    log.info("Calibración %s: %d/60 muestras válidas", name, len(samples))
    if len(samples) < 60:
        return False
    references[name] = [
        sum(row[i] for row in samples) / len(samples) for i in range(24)
    ]
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    reference_path.write_text(json.dumps(references, indent=2))
    log.info("Referencia guardada localmente, sin imágenes.")
    return True


def log_metrics(stats, since, now):
    summary = stats.summary()
    if summary:
        log.info(
            "Inferencia: cuadros=%d promedio=%.1f ms p95=%.1f ms máx=%.1f ms fps=%.1f",
            summary["frames"],
            summary["mean_ms"],
            summary["p95_ms"],
            summary["max_ms"],
            summary["frames"] / (now - since),
        )
    stats.reset()


def main():
    a = args_parser().parse_args()
    setup_logging(a.log_file)
    try:
        fall_config = config_from_args(a)
    except (OSError, ValueError, TypeError) as exc:
        raise SystemExit(f"Configuración de caídas inválida: {exc}")
    bed_zone, bed_config = bed_from_args(a)
    monitor_config = monitor_config_from_args(a)
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    token = os.environ.get("VIGIA_NODE_TOKEN", "")
    check_server(a, token)
    reference_path = Path(a.references)
    references = (
        json.loads(reference_path.read_text()) if reference_path.exists() else {}
    )
    uplink = None if a.calibrate else Uplink(a.server, token)
    monitor = None if a.calibrate else Monitor(
        references, a.immobility_minutes * 60, fall_config, uplink,
        bed_zone=bed_zone, bed_config=bed_config, monitor_config=monitor_config,
    )
    source = int(a.camera) if a.camera.isdigit() else a.camera
    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=a.model),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=2,
        min_pose_detection_confidence=0.7,
        min_pose_presence_confidence=0.7,
        min_tracking_confidence=0.7,
    )
    samples, paused = [], False
    stats, metrics_since = LatencyStats(), time.monotonic()
    camera = None
    if uplink:
        uplink.start()
    try:
        with vision.PoseLandmarker.create_from_options(options) as detector:
            while True:
                now = time.monotonic()
                if uplink and not uplink.lease_active(now):
                    # Fail closed; pending observations stay queued for later.
                    if camera:
                        camera.release()
                        camera = None
                    if not paused:
                        monitor.reset()
                        paused = True
                        log.warning(
                            "Monitoreo detenido: sin permiso o conexión al servidor."
                        )
                    time.sleep(0.5)
                    continue
                if paused:
                    paused = False
                    log.info("Monitoreo reanudado.")
                if camera is None:
                    camera = monitoring.Camera(source, cv2.VideoCapture, time.monotonic)
                frame = camera.read()
                if frame is None:
                    if camera.ended:
                        log.info("Fin del video local.")
                        break
                    # A live camera is reopened; no immobility is inferred meanwhile.
                    if monitor:
                        monitor.tick(now)
                    time.sleep(0.2)
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                started = time.perf_counter()
                result = detector.detect_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb),
                    int(now * 1000),
                )
                stats.add((time.perf_counter() - started) * 1000)
                if now - metrics_since >= a.metrics_seconds:
                    log_metrics(stats, metrics_since, now)
                    metrics_since = now
                landmarks, image_landmarks = [], []
                # Only one person in view; two people make geometry ambiguous.
                if len(result.pose_world_landmarks) == 1:
                    landmarks = as_dicts(result.pose_world_landmarks[0])
                    image_landmarks = as_dicts(result.pose_landmarks[0])
                if a.calibrate:
                    if calibration_step(
                        samples, landmarks, a.calibrate, references, reference_path
                    ):
                        break
                    continue
                monitor.process(
                    landmarks, image_landmarks, now, frame.shape[1] / frame.shape[0],
                    brightness=monitoring.frame_brightness(frame),
                    people=len(result.pose_world_landmarks),
                )
                time.sleep(0.05)
    finally:
        if camera:
            camera.release()
        if uplink:
            uplink.stop()


if __name__ == "__main__":
    main()
