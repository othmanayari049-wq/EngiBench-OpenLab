from __future__ import annotations

from collections import deque
from threading import RLock

from .models import TelemetrySample


class SampleBuffer:
    """Thread-safe bounded telemetry buffer."""

    def __init__(self, maxlen: int = 2000) -> None:
        if maxlen <= 0:
            raise ValueError("maxlen must be positive")
        self._samples: deque[TelemetrySample] = deque(maxlen=maxlen)
        self._lock = RLock()

    def append(self, sample: TelemetrySample) -> None:
        with self._lock:
            self._samples.append(sample)

    def snapshot(self) -> list[TelemetrySample]:
        with self._lock:
            return list(self._samples)

    def clear(self) -> None:
        with self._lock:
            self._samples.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._samples)
