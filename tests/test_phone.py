import math

import pytest

from engibench.phone import (
    PhoneBridgeError,
    discover_phyphox_buffers,
    normalize_phyphox_url,
    parse_phyphox_values,
)


def test_normalize_phyphox_url_adds_http():
    assert normalize_phyphox_url("192.168.1.42:8080/") == "http://192.168.1.42:8080"


def test_normalize_phyphox_url_rejects_unsupported_scheme():
    with pytest.raises(PhoneBridgeError):
        normalize_phyphox_url("ftp://192.168.1.42")


def test_discover_prefers_export_buffers():
    config = {
        "buffers": [{"name": "raw"}, {"name": "time"}, {"name": "x"}],
        "export": [
            {
                "set": "Acceleration",
                "data": [
                    {"label": "Time", "buffer": "time"},
                    {"label": "X", "buffer": "x"},
                    {"label": "X duplicate", "buffer": "x"},
                ],
            }
        ],
    }
    assert discover_phyphox_buffers(config) == ["time", "x"]


def test_discover_falls_back_to_declared_buffers():
    config = {"buffers": [{"name": "a"}, {"name": "b"}]}
    assert discover_phyphox_buffers(config) == ["a", "b"]


def test_parse_phyphox_values_uses_latest_finite_value():
    payload = {
        "buffer": {
            "x": {"buffer": [1, 2.5, None]},
            "y": {"buffer": [math.nan, 4]},
        },
        "status": {"measuring": True, "session": "abc"},
    }
    values, status = parse_phyphox_values(payload, ["x", "y"])
    assert values == {"x": 2.5, "y": 4.0}
    assert status["measuring"] is True
