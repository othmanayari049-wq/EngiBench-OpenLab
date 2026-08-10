from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from .models import TelemetrySample


def channel_series(samples: list[TelemetrySample]) -> dict[str, list[float]]:
    channels: dict[str, list[float]] = defaultdict(list)
    for sample in samples:
        for name, value in sample.values.items():
            channels[name].append(float(value))
    return dict(channels)


def channel_statistics(samples: list[TelemetrySample]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for name, values in channel_series(samples).items():
        arr = np.asarray(values, dtype=float)
        if arr.size == 0:
            continue
        result[name] = {
            "latest": float(arr[-1]),
            "mean": float(arr.mean()),
            "min": float(arr.min()),
            "max": float(arr.max()),
            "std": float(arr.std(ddof=0)),
            "rms": float(math.sqrt(float(np.mean(np.square(arr))))),
        }
    return result


def estimate_sample_rate(samples: list[TelemetrySample]) -> float | None:
    if len(samples) < 2:
        return None
    timestamps = np.asarray([sample.timestamp for sample in samples], dtype=float)
    diffs = np.diff(timestamps)
    diffs = diffs[diffs > 0]
    if diffs.size == 0:
        return None
    period = float(np.median(diffs))
    return 1.0 / period if period > 0 else None
