<div align="center">

# EngiBench OpenLab

### An open-source engineering workbench for embedded systems, electronics, phone sensors, data acquisition, and mechatronics.

[![CI](https://github.com/othmanayari049-wq/EngiBench-OpenLab/actions/workflows/ci.yml/badge.svg)](https://github.com/othmanayari049-wq/EngiBench-OpenLab/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](CHANGELOG.md)
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

Version **0.2.0** supports three acquisition paths:

- a built-in simulator for hardware-free testing;
- USB serial devices such as Arduino and ESP32 boards;
- **iOS and Android phones** through the phyphox Remote Access REST interface.

All three feed the same analysis pipeline, so plots, statistics, buffering, recording, and CSV export behave consistently regardless of the source.

## Features

- **Arduino and ESP32 friendly** — read newline-delimited telemetry over USB serial.
- **iOS and Android phone sensors** — connect to a phyphox experiment over the local network.
- **Automatic phone buffer discovery** — prefer buffers selected by the phyphox experiment author for export.
- **Manual phone buffer selection** — override discovery with comma-separated buffer names when needed.
- **Phone experiment status** — show connection state, experiment name, active buffers, paused/running state, and empty polls.
- **Hardware-free demo mode** — test EngiBench without owning a board or phone setup.
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
- **CLI utilities** — inspect serial ports or test serial telemetry parsing from the terminal.
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

Start with **Demo simulator** to verify the application before connecting hardware.

## Data Sources

### Demo simulator

The simulator creates three synthetic channels:

```text
temperature_C
voltage_V
current_A
```

Use it to test plotting, statistics, recording, buffer clearing, and CSV export without hardware.

### Serial device

Connect a supported serial board to the computer, choose **Serial device**, select the detected port and baud rate, then press **Start**.

The recommended serial format is one JSON object per line:

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

Unnamed values become `ch1`, `ch2`, `ch3`, and so on. See [`docs/PROTOCOL.md`](docs/PROTOCOL.md).

### Phone (iOS / Android)

EngiBench uses **phyphox Remote Access** for phone measurements. phyphox is available for iOS and Android and exposes the active experiment through a local REST interface when Remote Access is enabled.

The integration reads:

- `/config` to identify the experiment and discover useful buffers;
- `/get` to retrieve the latest selected values and experiment status.

The exact sensors available depend on the phone hardware and the phyphox experiment you choose.

## iOS and Android Phone Setup

1. Install and open phyphox on your iPhone or Android phone.
2. Put the phone and the computer running EngiBench on the same trusted local network.
3. Open a phyphox experiment, such as an acceleration experiment.
4. Enable **Remote Access** in phyphox.
5. Copy the exact local address shown by phyphox, for example:

```text
http://192.168.1.42:8080
```

6. In EngiBench choose **Phone (iOS / Android)**.
7. Paste the address into **Phone Remote Access URL**.
8. Leave **Buffer names** empty for automatic discovery, or enter known names separated by commas.
9. Select the polling interval and press **Start**.
10. If EngiBench says the experiment is paused, start the measurement in phyphox.

The official phyphox documentation notes that Remote Access is intended for devices on the same network. Its REST documentation also states that iPhones normally serve the interface on port 80, while an Android example uses port 8080; always use the exact address shown by the app instead of guessing a port.

For a detailed guide, see [`docs/PHONE.md`](docs/PHONE.md).

### Phone security note

phyphox documents that its Remote Access interface is **not encrypted or password protected**. Use this integration only on a trusted local network and do not expose the phone's Remote Access endpoint directly to the public internet.

Official references:

- [phyphox](https://phyphox.org/)
- [phyphox Remote Control](https://phyphox.org/remote-control/)
- [phyphox Remote-interface communication](https://www.phyphox.org/wiki/index.php/Remote-interface_communication)

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

## Dashboard Behavior

EngiBench intentionally prevents common lab mistakes:

- switching the selected source or source settings stops the previous acquisition;
- incompatible buffered data is cleared when the acquisition configuration changes;
- simulator values are explicitly labeled as simulated;
- serial Start is disabled when no serial port is detected;
- phone Start is disabled until a Remote Access URL is entered;
- recording is stopped when acquisition stops or unexpectedly ends;
- the buffer cannot be cleared while a recording is active;
- the most recent recording path remains visible after recording stops.

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
Arduino / ESP32          iPhone / Android          Simulator
      |                         |                      |
      | USB serial             | phyphox REST         |
      v                         v                      v
 SerialReader              PhyphoxReader         DemoSimulator
      \                         |                     /
       \________________________|____________________/
                                |
                                v
                     TelemetryController
                       |               |
                       v               v
                  SampleBuffer      CSVRecorder
                       |
                       v
                Statistics / Export
                       |
                       v
                Streamlit Dashboard
```

Every acquisition source emits the same `TelemetrySample` model. That keeps the analysis and UI independent from the transport and makes future sources easier to add.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for more detail.

## Repository Structure

```text
EngiBench-OpenLab/
├── app.py
├── pyproject.toml
├── CHANGELOG.md
├── src/engibench/
│   ├── buffer.py
│   ├── cli.py
│   ├── controller.py
│   ├── export.py
│   ├── models.py
│   ├── parser.py
│   ├── phone.py
│   ├── recording.py
│   ├── serial_io.py
│   ├── simulator.py
│   └── statistics.py
├── firmware/
│   ├── arduino_json/
│   └── esp32_json/
├── tests/
│   ├── test_buffer.py
│   ├── test_controller.py
│   ├── test_parser.py
│   ├── test_phone.py
│   ├── test_recording.py
│   ├── test_serial_io.py
│   └── test_statistics.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PHONE.md
│   ├── PROTOCOL.md
│   └── ROADMAP.md
├── examples/
└── .github/
```

## Testing

Run the test suite:

```bash
pytest -q
```

Run linting:

```bash
ruff check .
```

GitHub Actions runs both automatically on pushes to `main` and on pull requests across Python 3.10, 3.11, and 3.12.

## Roadmap

- **v0.1 — Foundation:** simulator, serial telemetry, plots, statistics, CSV recording/export, Arduino/ESP32 examples, CI.
- **v0.1.1 — Reliability:** safer source switching, session isolation, clearer connection/recording state, readable chart time axis.
- **v0.2 — Mobile Lab:** iOS and Android phone sensors through phyphox Remote Access, automatic buffer discovery, phone diagnostics.
- **Next — Lab workflows:** calibration, channel metadata/units, alarms, experiment templates, saved sessions.
- **Later — Signal lab:** FFT, filtering, peak detection, correlation.
- **Later — Mechatronics:** PID response analysis, motors/encoders, IMU visualization, ROS 2 integration.
- **Long term — Platform:** plugin API, automated lab reports, board compile/upload workflow, and community experiments.

Track the detailed plan in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Who Is It For?

- Computer Engineering students building embedded systems.
- Electrical Engineering students collecting and analyzing measurements.
- Mechatronics students working with sensors, actuators, control, and robotics.
- Students who want to use their phone as a portable measurement platform.
- Makers and educators who want a lightweight, open telemetry workbench.

## Contributing

Contributions are welcome. Useful areas include phone experiment support, sensor calibration, signal processing, board integrations, experiment templates, UI improvements, documentation, and testing.

Read [`CONTRIBUTING.md`](CONTRIBUTING.md), choose or open an issue, create a focused branch, and submit a pull request.

## Project Status

EngiBench OpenLab is an **early-stage open-source project**. The core telemetry pipeline, serial source, simulator, phone source, live analysis, recording, and CI are implemented. Real-world behavior can still vary with operating system, USB driver, board firmware, phone model, network configuration, and phyphox experiment.

If you report a problem, include the data source, operating system, board or phone model where relevant, configuration, and a reproducible telemetry example.

## License

Released under the [MIT License](LICENSE).

The optional phone integration communicates with the separately installed phyphox application through its documented Remote Access interface; EngiBench does not bundle phyphox.

---

<div align="center">

Built as an open engineering toolkit for learning by **measuring, testing, and experimenting**.

**If EngiBench helps your lab or project, star the repository and consider contributing a sensor workflow, phone experiment, or hardware integration.**

</div>
