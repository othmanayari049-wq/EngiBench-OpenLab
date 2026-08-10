import pytest

from engibench.parser import TelemetryParseError, parse_line


def test_json_parser():
    sample = parse_line('{"temperature_C":25.4,"voltage_V":3.31}', source="test")
    assert sample.values["temperature_C"] == 25.4
    assert sample.values["voltage_V"] == 3.31


def test_json_timestamp():
    sample = parse_line('{"timestamp":123.5,"x":2}')
    assert sample.timestamp == 123.5
    assert sample.values == {"x": 2.0}


def test_key_value_parser():
    sample = parse_line("x=1.5,y=-2")
    assert sample.values == {"x": 1.5, "y": -2.0}


def test_numeric_csv_parser():
    sample = parse_line("1,2.5,-3")
    assert sample.values == {"ch1": 1.0, "ch2": 2.5, "ch3": -3.0}


def test_invalid_line_rejected():
    with pytest.raises(TelemetryParseError):
        parse_line("hello world")
