# Architecture

EngiBench OpenLab separates acquisition, data handling, analysis, and presentation so different hardware and network transports can feed the same measurement pipeline.

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

## Design principles

- **Transport-independent telemetry:** every acquisition source emits `TelemetrySample` objects.
- **Named channels:** serial JSON fields and phyphox buffer names become EngiBench channel names.
- **Thread-safe acquisition:** serial, phone, and simulator sources run in background threads while the UI reads snapshots and status properties.
- **Bounded memory:** the live buffer has a fixed maximum length.
- **Source isolation:** changing acquisition configuration stops the previous source and clears incompatible buffered data.
- **Session isolation:** each Streamlit browser session owns its own controller and acquisition state.
- **Recording follows acquisition:** recording stops when acquisition stops or unexpectedly ends.
- **Deterministic analysis:** statistics are calculated locally; no AI or cloud service is required.

## Serial acquisition

`SerialReader` opens a selected serial port, reads newline-delimited records, parses supported telemetry formats, and emits valid samples. Connection state, errors, received-sample counts, and dropped-line counts are stored in thread-safe state for the UI.

## Phone acquisition

`PhyphoxReader` connects to the Remote Access web server provided by the separately installed phyphox app on iOS or Android.

It uses the documented phyphox endpoints:

- `/config` to identify the current experiment and discover useful buffers;
- `/get` to retrieve the latest values and experiment status.

EngiBench prefers buffers selected by the experiment author for export, then falls back to declared experiment buffers. Users can manually override the selected buffer names. If the phyphox session identifier changes because the user switches experiments, the reader reloads the configuration automatically.

Phone polling uses the local network and does not require the phone to appear as a USB serial/COM device.

See [`PHONE.md`](PHONE.md) for setup and security guidance.

## Simulator

`DemoSimulator` generates synthetic temperature, voltage, and current channels. It is intended for UI testing, development, demonstrations, and first-run verification without hardware.

## Controller and recording

`TelemetryController` receives samples from any acquisition source, appends them to `SampleBuffer`, and forwards them to `CSVRecorder` while recording is active. The controller exposes current and most-recent recording paths for UI feedback.

## Analysis and presentation

The dashboard converts buffered samples to a dataframe for live plotting and tabular display. Statistics are calculated by the analysis module, while CSV export can be generated from the current buffer without changing the acquisition source.

## Extension points

Potential future sources include Bluetooth, MQTT, ROS 2, and file replay. Planned analysis modules include calibration, channel metadata/units, FFT, filtering, threshold alarms, PID evaluation, and reusable experiment templates.
