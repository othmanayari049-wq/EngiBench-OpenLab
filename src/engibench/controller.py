from __future__ import annotations

from pathlib import Path
from threading import RLock

from .buffer import SampleBuffer
from .models import TelemetrySample
from .recording import CSVRecorder


class TelemetryController:
    """Coordinates buffering and optional recording for all acquisition sources."""

    def __init__(self, max_samples: int = 2000) -> None:
        self.buffer = SampleBuffer(max_samples)
        self._recorder: CSVRecorder | None = None
        self._last_recording_path: Path | None = None
        self._lock = RLock()

    def ingest(self, sample: TelemetrySample) -> None:
        self.buffer.append(sample)
        with self._lock:
            if self._recorder:
                self._recorder.write(sample)

    def start_recording(self, path: str | Path) -> None:
        samples = self.buffer.snapshot()
        channels = sorted({key for sample in samples for key in sample.values})
        if not channels:
            raise ValueError("Wait for at least one telemetry sample before recording")
        with self._lock:
            if self._recorder is not None:
                raise ValueError("A recording is already active")
            self._recorder = CSVRecorder(path, channels)
            self._last_recording_path = self._recorder.path

    def stop_recording(self) -> None:
        with self._lock:
            self._recorder = None

    @property
    def recording(self) -> bool:
        with self._lock:
            return self._recorder is not None

    @property
    def recording_path(self) -> Path | None:
        with self._lock:
            return self._recorder.path if self._recorder else None

    @property
    def last_recording_path(self) -> Path | None:
        with self._lock:
            return self._last_recording_path
