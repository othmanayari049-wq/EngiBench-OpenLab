# Changelog

All notable user-facing changes to EngiBench OpenLab are documented here.

## 0.2.1 - 2026-08-10

### Added

- One-click local-network discovery for iOS and Android phones running phyphox Remote Access.
- Automatic detection of the phone's phyphox endpoint without typing an IP address, URL, or port.
- Automatic experiment identification through phyphox `/config`.
- Automatic channel discovery from phyphox export/declared buffers.
- Automatic request to start the phyphox measurement after connection.
- Multiple-phone detection with explicit selection when discovery is ambiguous.
- `psutil`-based interface/netmask discovery so EngiBench scans the actual local IPv4 network rather than assuming a fixed subnet.
- Bounded scanning behavior for large campus/VPN networks.

### Changed

- Removed manual phone URL, buffer-name, and polling controls from the normal dashboard workflow.
- Updated phone documentation, architecture, roadmap, and README for the zero-config workflow.

## 0.2.0 - 2026-08-10

### Added

- iOS and Android phone sensor source through phyphox Remote Access.
- Automatic experiment/buffer discovery after a phone URL was supplied.
- Phone connection, experiment, buffer, measuring, and polling status.

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
