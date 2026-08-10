from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterable
from threading import Event, Lock, Thread
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .models import TelemetrySample


class PhoneBridgeError(RuntimeError):
    """Raised when a phyphox phone endpoint cannot be used safely."""


def normalize_phyphox_url(url: str) -> str:
    """Normalize and validate a phyphox Remote Access base URL."""
    text = url.strip()
    if not text:
        raise PhoneBridgeError("Enter the Remote Access address shown by phyphox.")
    if "://" not in text:
        text = f"http://{text}"

    parts = urlsplit(text)
    if parts.scheme not in {"http", "https"}:
        raise PhoneBridgeError("Phone URL must use http:// or https://.")
    if not parts.hostname:
        raise PhoneBridgeError("Phone URL is missing a valid host or IP address.")
    if parts.username or parts.password:
        raise PhoneBridgeError("Credentials are not supported in the phone URL.")

    clean_path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme, parts.netloc, clean_path, "", ""))


def _append_unique(target: list[str], value: str) -> None:
    name = value.strip()
    if name and name not in target:
        target.append(name)


def discover_phyphox_buffers(config: dict[str, object], *, limit: int = 12) -> list[str]:
    """Prefer buffers selected by the experiment author for export, then fall back."""
    names: list[str] = []

    def walk_export(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "buffer" and isinstance(value, str):
                    _append_unique(names, value)
                else:
                    walk_export(value)
        elif isinstance(node, list):
            for item in node:
                walk_export(item)

    walk_export(config.get("export", []))

    if not names:
        raw_buffers = config.get("buffers", [])
        if isinstance(raw_buffers, list):
            for entry in raw_buffers:
                if isinstance(entry, dict):
                    name = entry.get("name")
                    if isinstance(name, str):
                        _append_unique(names, name)

    return names[:limit]


def parse_phyphox_values(
    payload: dict[str, object],
    requested_buffers: Iterable[str],
) -> tuple[dict[str, float], dict[str, object]]:
    """Extract the latest finite value for each requested phyphox buffer."""
    values: dict[str, float] = {}
    raw_buffer_map = payload.get("buffer", {})

    if isinstance(raw_buffer_map, dict):
        for name in requested_buffers:
            entry = raw_buffer_map.get(name)
            if not isinstance(entry, dict):
                continue
            raw_values = entry.get("buffer", [])
            if not isinstance(raw_values, list):
                continue
            for raw_value in reversed(raw_values):
                if isinstance(raw_value, bool):
                    continue
                try:
                    numeric = float(raw_value)
                except (TypeError, ValueError):
                    continue
                if math.isfinite(numeric):
                    values[name] = numeric
                    break

    status = payload.get("status", {})
    return values, status if isinstance(status, dict) else {}


class PhyphoxReader:
    """Poll phone sensors from phyphox Remote Access on iOS or Android."""

    def __init__(
        self,
        base_url: str,
        callback: Callable[[TelemetrySample], None],
        *,
        poll_interval: float = 0.25,
        buffers: Iterable[str] | None = None,
        timeout: float = 2.0,
    ) -> None:
        if poll_interval < 0.05:
            raise PhoneBridgeError("Phone polling interval must be at least 0.05 seconds.")
        if timeout <= 0:
            raise PhoneBridgeError("Phone request timeout must be positive.")

        self.base_url = normalize_phyphox_url(base_url)
        self.callback = callback
        self.poll_interval = float(poll_interval)
        self.timeout = float(timeout)
        self.requested_buffers = tuple(
            name.strip() for name in (buffers or ()) if name and name.strip()
        )

        self._stop = Event()
        self._connected = Event()
        self._thread: Thread | None = None
        self._state_lock = Lock()
        self._last_error: str | None = None
        self._experiment_title = ""
        self._buffers: tuple[str, ...] = ()
        self._measuring: bool | None = None
        self._session: str | None = None
        self._received_samples = 0
        self._dropped_polls = 0

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
    def experiment_title(self) -> str:
        with self._state_lock:
            return self._experiment_title

    @property
    def buffers(self) -> tuple[str, ...]:
        with self._state_lock:
            return self._buffers

    @property
    def measuring(self) -> bool | None:
        with self._state_lock:
            return self._measuring

    @property
    def received_samples(self) -> int:
        with self._state_lock:
            return self._received_samples

    @property
    def dropped_polls(self) -> int:
        with self._state_lock:
            return self._dropped_polls

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._connected.clear()
        with self._state_lock:
            self._last_error = None
            self._measuring = None
            self._session = None
            self._received_samples = 0
            self._dropped_polls = 0
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=max(1.0, self.timeout + 0.25))

    def _request_json(self, endpoint: str) -> dict[str, object]:
        url = f"{self.base_url}{endpoint}"
        request = Request(url, headers={"User-Agent": "EngiBench-OpenLab/0.2"})
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                raw = response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise PhoneBridgeError(f"Cannot reach phyphox at {self.base_url}: {exc}") from exc

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PhoneBridgeError("phyphox returned an invalid JSON response.") from exc
        if not isinstance(payload, dict):
            raise PhoneBridgeError("phyphox returned an unexpected response format.")
        return payload

    def _load_configuration(self) -> tuple[str, tuple[str, ...]]:
        config = self._request_json("/config")
        title_raw = config.get("localTitle") or config.get("title") or "phyphox experiment"
        title = str(title_raw)
        discovered = self.requested_buffers or tuple(discover_phyphox_buffers(config))
        if not discovered:
            raise PhoneBridgeError(
                "No usable phyphox buffers were discovered. Enter buffer names manually."
            )
        return title, tuple(discovered)

    def _set_configuration(self, title: str, buffers: tuple[str, ...]) -> None:
        with self._state_lock:
            self._experiment_title = title
            self._buffers = buffers

    def _set_status(self, status: dict[str, object]) -> bool:
        session_raw = status.get("session")
        session = str(session_raw) if session_raw is not None else None
        measuring_raw = status.get("measuring")
        measuring = measuring_raw if isinstance(measuring_raw, bool) else None

        with self._state_lock:
            previous_session = self._session
            self._session = session
            self._measuring = measuring
        return bool(previous_session and session and previous_session != session)

    def _set_error(self, message: str) -> None:
        with self._state_lock:
            self._last_error = message

    def _increment_received(self) -> None:
        with self._state_lock:
            self._received_samples += 1

    def _increment_dropped(self) -> None:
        with self._state_lock:
            self._dropped_polls += 1

    def _run(self) -> None:
        try:
            title, buffers = self._load_configuration()
            self._set_configuration(title, buffers)
            self._connected.set()

            while not self._stop.is_set():
                with self._state_lock:
                    active_buffers = self._buffers

                query = "&".join(quote(name, safe="") for name in active_buffers)
                payload = self._request_json(f"/get?{query}")
                values, status = parse_phyphox_values(payload, active_buffers)

                session_changed = self._set_status(status)
                if session_changed:
                    title, buffers = self._load_configuration()
                    self._set_configuration(title, buffers)
                    self._stop.wait(self.poll_interval)
                    continue

                if values:
                    host = urlsplit(self.base_url).hostname or "phone"
                    self.callback(TelemetrySample(values=values, source=f"phone:{host}"))
                    self._increment_received()
                else:
                    self._increment_dropped()

                self._stop.wait(self.poll_interval)
        except PhoneBridgeError as exc:
            if not self._stop.is_set():
                self._set_error(str(exc))
        finally:
            self._connected.clear()
