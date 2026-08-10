# Changelog

All notable user-facing changes to EngiBench OpenLab are documented here.

## 0.2.0 - 2026-08-10

### Added

- Added **Phone (iOS / Android)** as a third acquisition source.
- Added `PhyphoxReader` for live phone measurements through the phyphox Remote Access REST interface.
- Added automatic phone experiment discovery through `/config`.
- Added automatic selection of experiment export buffers with fallback to declared buffers.
- Added optional manual phone buffer selection.
- Added phone poll-interval control.
- Added live phone status for connection, experiment title, active buffers, paused/running measurement state, and polls without usable values.
- Added automatic configuration reload when the phyphox session identifier changes after switching experiments.
- Added `docs/PHONE.md` with iOS/Android setup, troubleshooting, polling behavior, and security guidance.
- Added phone bridge tests for URL validation, buffer discovery, and value extraction.

### Documentation

- Reworked the README for version 0.2.0 and documented simulator, serial, iOS, and Android workflows.
- Updated the architecture diagram and design notes for phone acquisition.
- Updated the roadmap to mark Mobile Lab support as implemented.
- Documented that phyphox Remote Access should be used only on a trusted local network because the interface is not encrypted or password protected.

## 0.1.1 - 2026-08-10

### Fixed

- Stop the previous acquisition source automatically when the selected source, serial port, or baud rate changes.
- Clear incompatible buffered data when switching acquisition configurations so simulator and hardware samples are not mixed.
- Keep acquisition state isolated per browser session instead of sharing one cached controller across sessions.
- Report serial connection errors through thread-safe reader state rather than mutating Streamlit session state from a background thread.
- Expose serial connection state and ignored telemetry-line counts in the dashboard.
- Stop CSV recording when acquisition is stopped or unexpectedly ends.
- Preserve and display the most recent recording path.
- Disable serial start when no port is available and provide an explicit refresh-ports action.
- Use elapsed seconds on the live chart instead of raw Unix timestamps.
- Format recent telemetry timestamps as readable UTC times.
- Estimate sample rate from the recent window for a more responsive value.

### Tests

- Added controller tests for recording lifecycle and file-path state.
- Added a serial-reader test for surfaced connection errors.

## 0.1.0 - 2026-08-10

### Added

- Initial Streamlit telemetry dashboard.
- Demo simulator.
- USB serial acquisition for Arduino/ESP32-style devices.
- JSON, key/value, and numeric CSV telemetry parsing.
- Live plotting, statistics, sample-rate estimation, CSV recording, and CSV export.
- Arduino and ESP32 firmware examples.
- Initial tests, CI, documentation, contribution guide, and issue templates.
