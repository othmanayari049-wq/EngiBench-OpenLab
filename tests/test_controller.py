import csv

import pytest

from engibench.controller import TelemetryController
from engibench.models import TelemetrySample


def test_recording_requires_telemetry(tmp_path):
    ctl = TelemetryController()
    with pytest.raises(ValueError, match="at least one telemetry sample"):
        ctl.start_recording(tmp_path / "empty.csv")


def test_recording_path_and_last_path(tmp_path):
    ctl = TelemetryController()
    ctl.ingest(TelemetrySample({"voltage_V": 3.3}, timestamp=1.0, source="test"))
    path = tmp_path / "telemetry.csv"
    ctl.start_recording(path)
    assert ctl.recording
    assert ctl.recording_path == path
    assert ctl.last_recording_path == path

    ctl.ingest(TelemetrySample({"voltage_V": 3.4}, timestamp=2.0, source="test"))
    ctl.stop_recording()
    assert not ctl.recording
    assert ctl.recording_path is None
    assert ctl.last_recording_path == path

    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert float(rows[0]["voltage_V"]) == 3.4


def test_duplicate_recording_is_rejected(tmp_path):
    ctl = TelemetryController()
    ctl.ingest(TelemetrySample({"x": 1.0}))
    ctl.start_recording(tmp_path / "one.csv")
    with pytest.raises(ValueError, match="already active"):
        ctl.start_recording(tmp_path / "two.csv")
