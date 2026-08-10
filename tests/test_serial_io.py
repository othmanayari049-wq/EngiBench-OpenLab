from time import monotonic, sleep

import serial

from engibench.serial_io import SerialReader


def wait_until_stopped(reader: SerialReader, timeout: float = 1.0) -> None:
    deadline = monotonic() + timeout
    while reader.running and monotonic() < deadline:
        sleep(0.01)


def test_serial_reader_exposes_connection_error(monkeypatch):
    def fail_open(*_args, **_kwargs):
        raise serial.SerialException("port unavailable")

    monkeypatch.setattr(serial, "Serial", fail_open)
    reader = SerialReader("COM_TEST", 115200, lambda _sample: None)
    reader.start()
    wait_until_stopped(reader)

    assert not reader.running
    assert not reader.connected
    assert reader.last_error == "port unavailable"
    assert reader.received_samples == 0
    assert reader.dropped_lines == 0
