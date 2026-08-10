from engibench.buffer import SampleBuffer
from engibench.models import TelemetrySample


def test_buffer_is_bounded():
    buffer = SampleBuffer(maxlen=2)
    buffer.append(TelemetrySample({"x": 1}))
    buffer.append(TelemetrySample({"x": 2}))
    buffer.append(TelemetrySample({"x": 3}))
    assert [sample.values["x"] for sample in buffer.snapshot()] == [2, 3]
