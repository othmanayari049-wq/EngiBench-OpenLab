from __future__ import annotations

from collections.abc import Callable
from threading import Event, Lock, Thread

import serial
from serial.tools import list_ports

from .models import TelemetrySample
from .parser import TelemetryParseError, parse_line


def available_ports() -> list[str]:
    """Return serial device names currently visible to the operating system."""
    return [port.device for port in list_ports.comports()]


class SerialReader:
    """Background line-oriented serial reader with thread-safe status counters."""

    def __init__(
        self,
        port: str,
        baudrate: int,
        callback: Callable[[TelemetrySample], None],
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self._stop = Event()
        self._thread: Thread | None = None
        self._serial: serial.Serial | None = None
        self._state_lock = Lock()
        self._connected = Event()
        self._last_error: str | None = None
        self._received_samples = 0
        self._dropped_lines = 0

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    @property
    def last_error(self) -> str | None:
        with self._state_lock:
            return self._last_error

    @property
    def received_samples(self) -> int:
        with self._state_lock:
            return self._received_samples

    @property
    def dropped_lines(self) -> int:
        with self._state_lock:
            return self._dropped_lines

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._connected.clear()
        with self._state_lock:
            self._last_error = None
            self._received_samples = 0
            self._dropped_lines = 0
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._close_serial()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _close_serial(self) -> None:
        try:
            if self._serial and self._serial.is_open:
                self._serial.close()
        except (serial.SerialException, OSError):
            pass

    def _set_error(self, message: str) -> None:
        with self._state_lock:
            self._last_error = message

    def _increment_received(self) -> None:
        with self._state_lock:
            self._received_samples += 1

    def _increment_dropped(self) -> None:
        with self._state_lock:
            self._dropped_lines += 1

    def _run(self) -> None:
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=0.25)
            self._connected.set()
            while not self._stop.is_set():
                raw = self._serial.readline()
                if not raw:
                    continue
                try:
                    line = raw.decode("utf-8", errors="replace")
                    self.callback(parse_line(line, source=self.port))
                    self._increment_received()
                except TelemetryParseError:
                    self._increment_dropped()
        except (serial.SerialException, OSError) as exc:
            if not self._stop.is_set():
                self._set_error(str(exc))
        finally:
            self._connected.clear()
            self._close_serial()
