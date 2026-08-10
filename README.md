<div align="center">

# EngiBench OpenLab

### An open-source engineering workbench for embedded systems, electronics, phone sensors, data acquisition, and mechatronics.

[![CI](https://github.com/othmanayari049-wq/EngiBench-OpenLab/actions/workflows/ci.yml/badge.svg)](https://github.com/othmanayari049-wq/EngiBench-OpenLab/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-0.2.1-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![iOS + Android](https://img.shields.io/badge/Phone-iOS%20%2B%20Android-brightgreen.svg)](docs/PHONE.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Connect a board or a phone. Stream telemetry. Plot signals. Measure statistics. Record data. Learn from real experiments.**

[Features](#features) · [Quick Start](#quick-start) · [Data Sources](#data-sources) · [Phone Setup](#ios-and-android-phone-setup) · [Architecture](#architecture) · [Roadmap](#roadmap) · [Contributing](#contributing)

</div>

---

## What is EngiBench OpenLab?

Engineering students often jump between a serial monitor, plotting software, spreadsheets, scripts, and lab notes just to inspect a sensor experiment. **EngiBench OpenLab puts the core measurement workflow in one open-source toolkit** for Computer Engineering, Electrical Engineering, Embedded Systems, Robotics, and Mechatronics.

Version **0.2.1** supports three acquisition paths:

- a built-in simulator for hardware-free testing;
- USB serial devices such as Arduino and ESP32 boards;
- **iOS and Android phones with one-click local-network auto discovery** through phyphox Remote Access.

All three feed the same analysis pipeline, so plots, statistics, buffering, recording, and CSV export behave consistently regardless of the source.

## Features

- **Arduino and ESP32 friendly** — read newline-delimited telemetry over USB serial.
- **iOS and Android phone sensors** — use a phone as a live engineering sensor source.
- **One-click phone discovery** — no IP address, URL, port, or buffer names are required in the normal workflow.
- **Automatic experiment discovery** — EngiBench verifies phyphox through its `/config` endpoint and identifies the active experiment.
- **Automatic channel discovery** — EngiBench prefers buffers selected by the experiment author for export and falls back to declared experiment buffers.
- **Automatic phone measurement start** — after discovery, EngiBench asks phyphox to start the experiment through its documented control endpoint.
- **Multiple-phone handling** — if more than one phyphox phone is found, EngiBench shows the detected devices so the intended phone can be selected safely.
- **Hardware-free demo mode** — test EngiBench without owning a board or configuring a phone.
- **Flexible serial parser** — JSON, `key=value`, and plain numeric CSV formats.
- **Named channels** — work with fields such as `temperature_C`, `voltage_V`, `current_A`, `rpm`, or phone experiment buffer names.
- **Live multi-channel plots** — watch measurements change in real time.
- **Readable time axis** — live plots use elapsed seconds instead of raw Unix timestamps.
- **Engineering statistics** — latest, mean, minimum, maximum, population standard deviation, and RMS.
- **Sampling-rate estimate** — estimate the rate of samples entering EngiBench from recent timestamps.
- **CSV data logging** — record an active experiment to disk.
- **CSV export** — download the current in-memory buffer from the dashboard.
- **Source-safe switching** — changing source settings stops the old source and clears incompatible data to avoid mixing experiments.
- **Session isolation** — each browser session owns independent acquisition state.
- **Thread-safe acquisition** — background serial, phone, and simulator sources feed a bounded shared buffer.
- **Connection diagnostics** — surface serial errors, malformed serial lines, phone connection errors, and phone polls with no usable values.
- **Automated tests and CI** — GitHub Actions runs linting and tests on Python 3.10, 3.11, and 3.12.

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

### 4. Launch

```bash
streamlit run app.py
```

## Data Sources

### Demo simulator

Use **Demo simulator** to verify the complete dashboard without hardware. EngiBench generates simulated temperature, voltage, and current channels.

### Serial device

Choose **Serial device**, select the detected COM/TTY port and baud rate, then press **Start**. The recommended firmware format is one JSON object per line:

```json
{"temperature_C":25.4,"voltage_V":3.31,"current_A":0.12}
```

EngiBench also accepts `key=value` and unnamed numeric CSV telemetry. See [`docs/PROTOCOL.md`](docs/PROTOCOL.md).

### Phone (iOS / Android)

Phone setup is intentionally minimal in **0.2.1**.

On the phone:

1. Install/open **phyphox**.
2. Open an experiment, such as an acceleration experiment.
3. Enable **Remote Access**.

On the computer:

1. Choose **Phone (iOS / Android)**.
2. Press **Auto Detect & Start**.

That is the normal workflow. EngiBench automatically:

```text
Local network
    |
    +--> scan active private IPv4 network
            |
            +--> probe phyphox Remote Access ports 80 / 8080
                    |
                    +--> verify /config
                            |
                            +--> identify experiment
                            +--> detect useful buffers
                            +--> connect PhyphoxReader
                            +--> request measurement start
                            +--> live plots / statistics / CSV
```

There is no normal need to type an IP address, port, URL, buffer name, or polling interval.

#### Why Remote Access still has to be enabled

EngiBench cannot discover a phone before phyphox exposes its local Remote Access web server. This is a phyphox requirement, not an EngiBench form requirement. Once Remote Access is enabled, EngiBench handles discovery and connection automatically.

#### Local-network scope

Discovery uses the computer's active private/link-local IPv4 interfaces and their actual netmasks. Normal small networks are scanned directly. On very large campus/VPN networks, EngiBench limits discovery to the computer's local `/24` neighborhood instead of sweeping thousands of addresses.

#### Security

phyphox documents that Remote Access is not encrypted or password protected. Use the phone integration on a trusted local network and do not expose the phone's Remote Access service to the public internet.

More details: [`docs/PHONE.md`](docs/PHONE.md).

## CLI

After installation:

```bash
engibench ports
```

Parse a serial telemetry line locally:

```bash
engibench parse '{"temperature_C":25.4,"voltage_V":3.31}'
```

## Architecture

```text
Arduino / ESP32       iOS / Android           Simulator
      |                    |                      |
      | USB serial         | local network        |
      v                    v                      v
 SerialReader      Phone Auto Discovery     DemoSimulator
                           |
                      PhyphoxReader
      \                    |                     /
       \                   |                    /
        +---------- TelemetryController --------+
                         |        |
                         v        v
                   SampleBuffer  CSVRecorder
                         |
                         v
                 Statistics / Export
                         |
                         v
                 Streamlit Dashboard
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

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
│   ├── phone.py
│   ├── phone_discovery.py
│   ├── recording.py
│   ├── serial_io.py
│   ├── simulator.py
│   └── statistics.py
├── firmware/
├── tests/
├── docs/
└── .github/
```

## Testing

```bash
pytest -q
ruff check .
```

GitHub Actions executes linting and tests on Python 3.10, 3.11, and 3.12 for pushes and pull requests.

## Roadmap

- **v0.1 — Foundation:** simulator, serial telemetry, plots, statistics, CSV, firmware examples, tests and CI.
- **v0.1.1 — Reliability:** source-safe switching, session isolation, better status, readable time axis, recording lifecycle fixes.
- **v0.2 — Mobile lab:** iOS/Android phyphox source and phone experiment integration.
- **v0.2.1 — Zero-config phone workflow:** local-network discovery, automatic experiment/channel detection, and automatic measurement start.
- **v0.3 — Lab usability:** calibration, units, alarms, templates and saved sessions.
- **v0.4 — Board workflow:** Arduino CLI board discovery, compile/upload and presets.
- **v0.5 — Signal lab:** FFT, filters, peak detection and correlation.
- **v0.6 — Mechatronics:** PID analysis, motors/encoders, IMU visualization and ROS 2.
- **v1.0 — Platform:** plugin API, automated reports and community experiment library.

## Contributing

Contributions from students, educators, embedded developers and robotics enthusiasts are welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request.

## Project Status

EngiBench OpenLab is an early-stage open-source engineering toolkit. Automated tests validate the software core, but physical hardware and phone behavior can vary with operating system, firewall, Wi-Fi isolation, USB driver, phone model, and experiment configuration.

## License

Released under the [MIT License](LICENSE).

---

<div align="center">

Built as an open engineering toolkit for learning by measuring, testing, and experimenting.

**Star the repository if it helps your lab work, and consider contributing an experiment or hardware integration.**

</div>
