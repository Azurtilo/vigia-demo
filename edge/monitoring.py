"""Monitoring health of the node (spec 017): is the camera actually watching?

A blind detector must say so instead of failing silently (pose_app prototype).
Only booleans and one brightness number reach this module, never frames.
"""

import dataclasses
import logging

from . import options

log = logging.getLogger("vigia.edge")

NORMAL, LOST, NO_IMAGE, LOW_LIGHT = "normal", "persona_no_visible", "sin_imagen", "poca_luz"
STATES = (NORMAL, LOST, NO_IMAGE, LOW_LIGHT)
LIGHT_HYSTERESIS = 1.3  # back to "enough light" needs a bit more than the minimum
MAX_REOPEN_SECONDS = 30


@dataclasses.dataclass(frozen=True)
class MonitorConfig:
    lost_seconds: float = 10.0
    no_image_seconds: float = 10.0
    min_brightness: float = 0.12
    low_light_seconds: float = 5.0

    def __post_init__(self):
        options.check_positive(self)
        if self.min_brightness * LIGHT_HYSTERESIS > 1:
            raise ValueError("min_brightness debe ser menor que 0,77.")


def add_arguments(parser):
    options.add_arguments(
        parser, MonitorConfig, "monitor", "estado de monitoreo (spec 017)",
        "JSON local con umbrales del estado de monitoreo",
    )


def config_from_args(args):
    return options.config_from_args(args, MonitorConfig, "monitor", "monitoreo")


class MonitorStatus:
    """Effective state by priority: no image > low light > person lost > normal."""

    def __init__(self, config=None):
        self.config = config or MonitorConfig()
        self.reset()

    def reset(self):
        self.started = self.last_frame = self.last_person = None
        self.dark, self.light_since = False, None
        self.state = NORMAL

    def frame(self, now, person, brightness=None):
        """A processed frame; `person` is True when a usable person is in view."""
        if self.started is None:
            self.started = now
        self.last_frame = now
        if person:
            self.last_person = now
        if brightness is not None:
            self._light(brightness, now)
        return self._update(now)

    def tick(self, now):
        """Called while no frame arrives (camera lost); returns a new state or None."""
        if self.started is None:
            self.started = now
        return self._update(now)

    def _light(self, brightness, now):
        c = self.config
        if self.dark:
            toward = brightness >= c.min_brightness * LIGHT_HYSTERESIS
        else:
            toward = brightness < c.min_brightness
        if not toward:
            self.light_since = None
            return
        if self.light_since is None:
            self.light_since = now
        if now - self.light_since >= c.low_light_seconds:
            self.dark, self.light_since = not self.dark, None

    def _update(self, now):
        c = self.config
        last = self.last_frame if self.last_frame is not None else self.started
        if now - last >= c.no_image_seconds:
            state = NO_IMAGE
        elif self.dark:
            state = LOW_LIGHT
        elif self.last_person is not None and now - self.last_person >= c.lost_seconds:
            state = LOST  # only after the person was seen in this session
        else:
            state = NORMAL
        if state == self.state:
            return None
        self.state = state
        return state


class Camera:
    """A live camera that stops delivering frames is reopened with backoff.

    A local video file that ends is not reopened: `ended` turns True.
    """

    def __init__(self, source, opener, clock):
        self.source, self.opener, self.clock = source, opener, clock
        self.live = isinstance(source, int)
        self.capture, self.retry_at, self.backoff, self.ended = None, 0.0, 1.0, False

    def read(self):
        now = self.clock()
        if self.capture is None:
            if now < self.retry_at:
                return None
            self.capture = self.opener(self.source)
        ok, frame = self.capture.read()
        if ok:
            self.backoff = 1.0
            return frame
        self.release()
        if not self.live:
            self.ended = True
            return None
        log.warning("Sin imagen de cámara; se reintenta abrirla en %d s.", self.backoff)
        self.retry_at = now + self.backoff
        self.backoff = min(MAX_REOPEN_SECONDS, self.backoff * 2)
        return None

    def release(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None


def frame_brightness(frame):
    """Mean brightness 0..1 of a reduced grey copy; the copy is discarded."""
    import cv2

    height, width = frame.shape[:2]
    small = cv2.resize(frame, (160, max(1, round(160 * height / width))),
                       interpolation=cv2.INTER_AREA)
    return float(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).mean()) / 255
