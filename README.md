<div align="center">

# EngiBench OpenLab

### An open-source engineering workbench for embedded systems, electronics, sensors, data acquisition, and mechatronics.

[![CI](https://github.com/othmanayari049-wq/EngiBench-OpenLab/actions/workflows/ci.yml/badge.svg)](https://github.com/othmanayari049-wq/EngiBench-OpenLab/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-brightgreen.svg)](CONTRIBUTING.md)

**Connect a board. Stream telemetry. Plot signals. Measure statistics. Record data. Learn from real hardware.**

[Features](#features) · [Quick Start](#quick-start) · [Telemetry Protocol](#telemetry-protocol) · [Architecture](#architecture) · [Roadmap](#roadmap) · [Contributing](#contributing)

</div>

---

## Why EngiBench?

Engineering students often use several disconnected tools to inspect serial output, plot sensor data, calculate statistics, save measurements, and document experiments. **EngiBench OpenLab brings the core workflow into one open-source toolkit** that is designed to grow with Computer Engineering, Electrical Engineering, Embedded Systems, Robotics, and Mechatronics projects.

The project starts with a practical v0.1 foundation: serial telemetry and a hardware-free simulator feed a common analysis pipeline, while a Streamlit dashboard provides live plots, channel statistics, recent data, and CSV export.

## Features

- **Arduino and ESP32 friendly** — read newline-delimited telemetry over USB serial.
- **Hardware-free demo mode** — explore the dashboard without owning a board.
- **Flexible telemetry parser** — JSON, `key=value`, and plain numeric CSV formats.
- **Named sensor channels** — work with fields such as `temperature_C`, `voltage_V`, `current_A`, `rpm`, or custom names.
- **Live multi-channel plots** — watch measurements change in real time.
- **Engineering statistics** — latest, mean, minimum, maximum, population standard deviation, and RMS.
- **Sampling-rate estimate** — estimate acquisition frequency from sample timestamps.
- **CSV data logging** — record a running experiment to disk.
- **CSV export** — download the current in-memory buffer from the dashboard.
- **Thread-safe acquisition** — background serial/simulator sources feed a bounded shared buffer.
- **CLI utilities** — inspect serial ports or test telemetry parsing from the terminal.
- **Tested core** — parser, buffer, statistics, and recording modules have automated tests.
- **CI ready** — GitHub Actions tests Python 3.10, 3.11, and 3.12.

## Quick Start

### 1. Clone

```bash
git clone https://github.com/othmanayari049-wq/EngiBench-OpenLab.git
cd EngiBench-OpenLab
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install

```bash
pip install -e .
```

For development tools:

```bash
pip install -e ".[dev]"
```

### 4. Launch the dashboard

```bash
streamlit run app.py
```

Start with **Demo simulator** in the sidebar. When you have a board connected, switch to **Serial device**, select the port and baud rate, then press **Start**.

## Telemetry Protocol

The recommended format is one JSON object per line:

```json
{"temperature_C":25.4,"voltage_V":3.31,"current_A":0.12}
```

EngiBench also accepts:

```text
temperature_C=25.4,voltage_V=3.31,current_A=0.12
```

and unnamed numeric values:

```text
25.4,3.31,0.12
```

Unnamed values become `ch1`, `ch2`, `ch3`, and so on. See [`docs/PROTOCOL.md`](docs/PROTOCOL.md) for the protocol details.

## Arduino Example

A minimal Arduino sketch is included in [`firmware/arduino_json`](firmware/arduino_json/arduino_json.ino). It samples `A0`, converts the reading to voltage, and streams JSON at approximately 10 Hz.

```cpp
Serial.print("{\"analog_raw\":");
Serial.print(sensor, 0);
Serial.print(",\"voltage_V\":");
Serial.print(voltage, 3);
Serial.println("}");
```

An ESP32 ADC example is available in [`firmware/esp32_json`](firmware/esp32_json/esp32_json.ino).

## CLI

After installation:

```bash
engibench ports
```

Parse a telemetry line locally:

```bash
engibench parse '{"temperature_C":25.4,"voltage_V":3.31}'
```

## Architecture

```text
Arduino / ESP32 / Simulator
          |
          v
   Acquisition Layer
     /          \
SerialReader   Simulator
     \          /
      v        v
 TelemetryController
    |          |
    v          v
SampleBuffer  CSVRecorder
    |
    v
Statistics / Export
    |
    v
Streamlit Dashboard
```

The acquisition layer is intentionally separated from analysis and presentation. This keeps the core reusable as future transports such as Bluetooth, MQTT, file replay, or ROS 2 are added. More detail is available in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Repository Structure

```text
EngiBench-OpenLab/
├── app.py
├── pyproject.toml
├── src/engibench/
│   ├── buffer.py
│   ├── cli.py
│   ├── controller.py
│   ├── export.py
│   ├── models.py
│   ├── parser.py
│   ├── recording.py
│   ├── serial_io.py
│   ├── simulator.py
│   └── statistics.py
├── firmware/
│   ├── arduino_json/
│   └── esp32_json/
├── tests/
├── docs/
├── examples/
└── .github/
```

## Roadmap

- **v0.1 — Foundation:** serial telemetry, simulator, plots, statistics, CSV, Arduino/ESP32 examples, tests, CI.
- **v0.2 — Lab usability:** calibration, units/metadata, threshold alarms, experiment templates, saved sessions.
- **v0.3 — Board workflow:** Arduino CLI integration, board discovery, compile/upload, firmware presets.
- **v0.4 — Signal lab:** FFT, digital filtering, peak detection, correlation.
- **v0.5 — Mechatronics:** PID response analysis, motors/encoders, IMU visualization, ROS 2 integration.
- **v1.0 — Platform:** plugin API, automated lab reports, community experiment library.

Track the detailed plan in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Testing

```bash
pytest -q
```

Lint the code with:

```bash
ruff check .
```

GitHub Actions runs the test/lint workflow automatically for pushes to `main` and pull requests.

## Who Is It For?

- Computer Engineering students building embedded systems.
- Electrical Engineering students collecting and analyzing measurements.
- Mechatronics students working with sensors, actuators, control, and robotics.
- Makers and educators who want a lightweight, open telemetry workbench.

## Contributing

Contributions are welcome. Useful areas include sensor calibration, signal processing, board integrations, experiment templates, UI improvements, documentation, and testing.

Read [`CONTRIBUTING.md`](CONTRIBUTING.md), choose or open an issue, create a focused branch, and submit a pull request.

## Project Status

EngiBench OpenLab is currently an **early-stage v0.1 project**. The core telemetry pipeline is implemented, but hardware behavior can vary by operating system, USB/serial driver, board, and firmware. Please report reproducible issues with the board, OS, baud rate, and an example telemetry line.

## License

Released under the [MIT License](LICENSE).

---

<div align="center">

Built as an open engineering toolkit for learning by measuring, testing, and experimenting.

**Star the repository if you find it useful, and consider contributing an experiment or hardware integration.**

</div>
