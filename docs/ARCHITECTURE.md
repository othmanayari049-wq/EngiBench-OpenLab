# Architecture

EngiBench OpenLab separates acquisition, data handling, analysis, and presentation so new hardware transports can be added without rewriting the dashboard.

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

## Design principles

- **Transport-independent telemetry:** every source emits `TelemetrySample` objects.
- **Named channels:** sensor names and units travel as field names such as `temperature_C` or `voltage_V`.
- **Thread-safe acquisition:** serial input and simulation run in background threads while the UI reads snapshots.
- **Bounded memory:** the live buffer has a fixed maximum length.
- **Deterministic analysis:** statistics are calculated locally; no AI service is required.

## Extension points

Planned sources include Bluetooth, MQTT, ROS 2, and file replay. Planned analysis modules include calibration, FFT, filtering, threshold alarms, PID evaluation, and experiment templates.
