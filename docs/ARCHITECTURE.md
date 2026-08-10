# Architecture

EngiBench OpenLab separates acquisition, data handling, analysis, and presentation so new hardware transports can be added without rewriting the dashboard.

```text
Arduino / ESP32        iOS / Android          Simulator
      |                     |                    |
      | USB serial          | local network      |
      v                     v                    v
 SerialReader       Phone Auto Discovery    DemoSimulator
                            |
                       PhyphoxReader
      \                     |                    /
       \                    |                   /
        +----------- TelemetryController -------+
                          |       |
                          v       v
                    SampleBuffer CSVRecorder
                          |
                          v
                   Statistics / Export
                          |
                          v
                   Streamlit Dashboard
```

## Design principles

- **Transport-independent telemetry:** every source emits `TelemetrySample` objects.
- **Named channels:** sensor names and units travel as field names.
- **Zero-config phone path:** local-network discovery removes manual IP/URL and buffer configuration in the normal phone workflow.
- **Bounded discovery:** phone scans are limited to local private/link-local networks and bounded on unusually large subnets.
- **Thread-safe acquisition:** serial input, phone polling, and simulation run in background workers while the UI reads snapshots.
- **Bounded memory:** the live buffer has a fixed maximum length.
- **Deterministic analysis:** statistics are calculated locally; no AI service is required.

## Phone discovery

`phone_discovery.py` enumerates active IPv4 interfaces using `psutil`, derives their actual netmasks, scans local candidates concurrently, and identifies phyphox by validating its `/config` response. `PhyphoxReader` then discovers experiment buffers and polls `/get` for live values.

## Extension points

Planned transports include Bluetooth, MQTT, ROS 2, and file replay. Planned analysis modules include calibration, FFT, filtering, threshold alarms, PID evaluation, and experiment templates.
