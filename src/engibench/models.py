from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from time import time


@dataclass(frozen=True, slots=True)
class TelemetrySample:
    """One timestamped telemetry sample with named numeric channels."""

    values: Mapping[str, float]
    timestamp: float = field(default_factory=time)
    source: str = "unknown"
