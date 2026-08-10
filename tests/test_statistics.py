import pytest

from engibench.models import TelemetrySample
from engibench.statistics import channel_statistics, estimate_sample_rate


def test_channel_statistics():
    samples = [
        TelemetrySample({"x": 1.0}, timestamp=0.0),
        TelemetrySample({"x": 3.0}, timestamp=0.5),
    ]
    stats = channel_statistics(samples)["x"]
    assert stats["latest"] == 3.0
    assert stats["mean"] == 2.0
    assert stats["min"] == 1.0
    assert stats["max"] == 3.0


def test_sample_rate():
    samples = [
        TelemetrySample({"x": 1}, timestamp=1.0),
        TelemetrySample({"x": 2}, timestamp=1.1),
        TelemetrySample({"x": 3}, timestamp=1.2),
    ]
    assert estimate_sample_rate(samples) == pytest.approx(10.0)
