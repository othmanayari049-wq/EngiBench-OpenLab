from __future__ import annotations

import json
from typing import Iterable

from .models import TelemetrySample


class TelemetryParseError(ValueError):
    """Raised when an incoming telemetry line cannot be interpreted."""


def _numeric_mapping(items: Iterable[tuple[str, object]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for key, value in items:
        if key in {"timestamp", "time", "ts"}:
            continue
        if isinstance(value, bool):
            continue
        try:
            result[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return result


def parse_line(line: str, *, source: str = "serial") -> TelemetrySample:
    """Parse JSON, key=value, or numeric CSV telemetry into a sample."""

    text = line.strip()
    if not text:
        raise TelemetryParseError("Empty telemetry line")

    if text.startswith("{"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise TelemetryParseError("Invalid JSON telemetry") from exc
        if not isinstance(payload, dict):
            raise TelemetryParseError("JSON telemetry must be an object")
        values = _numeric_mapping(payload.items())
        if not values:
            raise TelemetryParseError("No numeric channels found")
        ts_raw = payload.get("timestamp", payload.get("time", payload.get("ts")))
        timestamp = float(ts_raw) if ts_raw is not None else None
        return TelemetrySample(values=values, timestamp=timestamp or __import__("time").time(), source=source)

    if "=" in text:
        pairs: list[tuple[str, object]] = []
        for chunk in text.split(","):
            if "=" not in chunk:
                continue
            key, value = chunk.split("=", 1)
            pairs.append((key.strip(), value.strip()))
        values = _numeric_mapping(pairs)
        if not values:
            raise TelemetryParseError("No numeric key=value channels found")
        return TelemetrySample(values=values, source=source)

    try:
        numbers = [float(part.strip()) for part in text.split(",")]
    except ValueError as exc:
        raise TelemetryParseError("Unsupported telemetry format") from exc
    if not numbers:
        raise TelemetryParseError("No values found")
    values = {f"ch{i + 1}": value for i, value in enumerate(numbers)}
    return TelemetrySample(values=values, source=source)
