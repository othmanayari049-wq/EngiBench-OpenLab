# Telemetry Protocol

EngiBench accepts one sample per line over serial.

## Recommended: JSON object

```json
{"temperature_C":25.4,"voltage_V":3.31,"current_A":0.12}
```

An optional `timestamp`, `time`, or `ts` field can provide a numeric timestamp. Other numeric keys become channels.

## Key/value format

```text
temperature_C=25.4,voltage_V=3.31,current_A=0.12
```

## Numeric CSV fallback

```text
25.4,3.31,0.12
```

Unnamed values are exposed as `ch1`, `ch2`, `ch3`, and so on.

## Recommendations

- Use newline-delimited records.
- Prefer JSON for self-describing telemetry.
- Keep channel names short and stable.
- Put units in the channel name when useful, e.g. `rpm`, `voltage_V`, `accel_x_mps2`.
- Use a consistent serial baud rate; the examples use 115200 baud.
