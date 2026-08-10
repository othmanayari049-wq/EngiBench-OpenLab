# iOS and Android phone support

EngiBench OpenLab can use an iPhone or Android phone as a live sensor source through the **phyphox Remote Access** interface.

This integration uses the phone's local network connection, not USB serial. The phone and the computer running EngiBench should normally be on the same Wi-Fi network.

## Requirements

- EngiBench OpenLab 0.2.0 or newer.
- The phyphox app on iOS or Android.
- Phone and computer on the same trusted local network.
- A phyphox experiment that exposes useful data buffers.

Official phyphox resources:

- https://phyphox.org/
- https://phyphox.org/remote-control/
- https://www.phyphox.org/wiki/index.php/Remote-interface_communication

## Setup

1. Open phyphox on the phone.
2. Open an experiment, for example an acceleration experiment.
3. Enable **Remote Access** from the phyphox menu.
4. phyphox displays a local address such as `http://192.168.1.42:8080`.
5. Open EngiBench and choose **Phone (iOS / Android)**.
6. Paste the address into **Phone Remote Access URL**.
7. Leave **Buffer names** empty for automatic discovery, or enter a comma-separated list such as `t,accX,accY,accZ` when you know the experiment's buffers.
8. Press **Start** in EngiBench.
9. If EngiBench says the experiment is paused, press the measurement/play control in phyphox.

The exact address and port are provided by phyphox. Do not guess them; use the address shown by the app.

## How EngiBench reads the phone

EngiBench uses phyphox's documented REST interface:

- `/config` identifies the current experiment and its available/export buffers.
- `/get` returns the latest values for the selected buffers and the measurement status.
- EngiBench prefers buffers chosen by the experiment author for export and falls back to declared experiment buffers when necessary.

The phone data then enters the same EngiBench pipeline as serial and simulated data:

```text
iPhone / Android
      |
      | phyphox Remote Access (local network)
      v
 PhyphoxReader
      |
      v
TelemetryController
      |
      +--> SampleBuffer --> plots / statistics / CSV export
      |
      +--> CSVRecorder
```

## Polling rate

The **Phone poll interval** controls how often EngiBench asks phyphox for the latest values. This is not necessarily the phone sensor's native sampling frequency. For example, a 0.25 s poll interval requests updates about four times per second, while the underlying phyphox experiment may sample the physical sensor at a different rate.

## Automatic buffer discovery

EngiBench first looks at the export buffers exposed by the experiment's `/config` response because these are the buffers selected by the experiment author for exported data. If none are available, EngiBench falls back to the declared experiment buffers.

If automatic discovery does not select the channels you want, use the optional **Buffer names** field in EngiBench.

## Security

phyphox documents that its Remote Access interface is not encrypted or password protected. Use the phone integration only on a trusted local network and do not expose the Remote Access endpoint directly to the public internet.

## Troubleshooting

### EngiBench cannot reach the phone

- Confirm Remote Access is still enabled in phyphox.
- Confirm both devices are on the same local network.
- Copy the exact address shown by phyphox.
- Check whether a firewall or guest Wi-Fi isolation prevents devices from talking to each other.

### Connected but no values appear

- Start the measurement in phyphox.
- Try a different phyphox experiment.
- Enter known buffer names manually.
- Check the EngiBench status message for dropped polls or a changed experiment.

### Switching experiments

phyphox changes its session identifier when the active experiment changes. EngiBench detects this and reloads the experiment configuration and buffer list automatically.
