import csv

from engibench.models import TelemetrySample
from engibench.recording import CSVRecorder


def test_csv_recording(tmp_path):
    path = tmp_path / "telemetry.csv"
    recorder = CSVRecorder(path, ["x", "y"])
    recorder.write(TelemetrySample({"x": 1.25, "y": 2.5}, timestamp=10.0, source="test"))
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["source"] == "test"
    assert float(rows[0]["x"]) == 1.25
