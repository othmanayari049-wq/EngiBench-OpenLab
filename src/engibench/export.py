from __future__ import annotations

import io

import pandas as pd

from .models import TelemetrySample


def samples_to_dataframe(samples: list[TelemetrySample]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for sample in samples:
        row: dict[str, object] = {"timestamp": sample.timestamp, "source": sample.source}
        row.update(sample.values)
        rows.append(row)
    return pd.DataFrame(rows)


def samples_to_csv_bytes(samples: list[TelemetrySample]) -> bytes:
    buffer = io.StringIO()
    samples_to_dataframe(samples).to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
