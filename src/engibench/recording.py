from __future__ import annotations

import csv
from pathlib import Path
from threading import RLock

from .models import TelemetrySample


class CSVRecorder:
    """Append telemetry to a CSV file with stable channel columns."""

    def __init__(self, path: str | Path, fieldnames: list[str]) -> None:
        self.path = Path(path)
        self.fieldnames = list(fieldnames)
        self._lock = RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["timestamp", "source", *self.fieldnames])
            writer.writeheader()

    def write(self, sample: TelemetrySample) -> None:
        row = {"timestamp": sample.timestamp, "source": sample.source}
        row.update({name: sample.values.get(name, "") for name in self.fieldnames})
        with self._lock, self.path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["timestamp", "source", *self.fieldnames])
            writer.writerow(row)
