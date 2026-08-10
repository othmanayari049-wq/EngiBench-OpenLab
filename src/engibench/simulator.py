from __future__ import annotations

import math
import random
import time
from collections.abc import Callable
from threading import Event, Thread

from .models import TelemetrySample


class DemoSimulator:
    """Hardware-free source that emits realistic demo sensor channels."""

    def __init__(self, callback: Callable[[TelemetrySample], None], interval: float = 0.1) -> None:
        self.callback = callback
        self.interval = interval
        self._stop = Event()
        self._thread: Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self) -> None:
        start = time.time()
        while not self._stop.is_set():
            t = time.time() - start
            sample = TelemetrySample(
                values={
                    "temperature_C": 25.0 + 1.4 * math.sin(t / 5) + random.uniform(-0.12, 0.12),
                    "voltage_V": 3.30 + 0.08 * math.sin(t * 1.7) + random.uniform(-0.01, 0.01),
                    "current_A": 0.18 + 0.04 * math.sin(t * 2.1) + random.uniform(-0.008, 0.008),
                },
                source="simulator",
            )
            self.callback(sample)
            self._stop.wait(self.interval)
