"""Per-frame latency statistics for the edge log and bench. No frames kept."""

import math


class LatencyStats:
    def __init__(self):
        self.samples = []

    def add(self, milliseconds):
        self.samples.append(milliseconds)

    def summary(self):
        if not self.samples:
            return None
        ordered = sorted(self.samples)
        return {
            "frames": len(ordered),
            "mean_ms": round(sum(ordered) / len(ordered), 2),
            # Nearest-rank percentile: an observed value, never interpolated.
            "p95_ms": round(ordered[math.ceil(0.95 * len(ordered)) - 1], 2),
            "max_ms": round(ordered[-1], 2),
        }

    def reset(self):
        self.samples.clear()
