from __future__ import annotations

from threading import Event, Thread
from typing import Callable

import serial
from serial.tools import list_ports

from .models import TelemetrySample
from .parser import TelemetryParseError, parse_line


def available_ports() -> list[str]:
    return [port.device for port in list_ports.comports()]


class SerialReader:
    """Background line-oriented serial reader."""

    def __init__(
        self,
        port: str,
        baudrate: int,
        callback: Callable[[TelemetrySample], None],
        error_callback: Callable[[str], None] | None = None,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.error_callback = error_callback
        self._stop = Event()
        self._thread: Thread | None = None
        self._serial: serial.Serial | None = None

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
        if self._serial and self._serial.is_open:
            self._serial.close()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self) -> None:
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=0.25)
            while not self._stop.is_set():
                raw = self._serial.readline()
                if not raw:
                    continue
                try:
                    line = raw.decode("utf-8", errors="replace")
                    self.callback(parse_line(line, source=self.port))
                except TelemetryParseError:
                    continue
        except Exception as exc:  # serial errors vary by OS/driver
            if self.error_callback:
                self.error_callback(str(exc))
        finally:
            if self._serial and self._serial.is_open:
                self._serial.close()
