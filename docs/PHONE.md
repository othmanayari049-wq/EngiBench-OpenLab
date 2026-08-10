# iOS and Android phone support

EngiBench OpenLab 0.2.1 can automatically discover an iPhone or Android phone running **phyphox Remote Access** on the same local network.

## Normal setup: no address or buffer names

On the phone:

1. Open phyphox.
2. Open an experiment, for example an acceleration experiment.
3. Enable **Remote Access**.

On the computer:

1. Open EngiBench.
2. Choose **Phone (iOS / Android)**.
3. Press **Auto Detect & Start**.

EngiBench then scans the local network, verifies compatible phyphox endpoints through `/config`, discovers the experiment's useful buffers, connects, and asks phyphox to start measuring.

## Why Remote Access is still required

phyphox only exposes its REST/web interface after Remote Access is enabled in the app. There is therefore nothing for EngiBench to discover before that switch is enabled. EngiBench removes the manual computer-side configuration, but it cannot bypass this phone-side phyphox requirement.

## Discovery behavior

EngiBench:

- reads active network interfaces and their IPv4 netmasks;
- considers private and link-local IPv4 networks;
- probes the common phyphox Remote Access HTTP ports 80 and 8080;
- requests `/config` to distinguish phyphox from unrelated web servers;
- uses the experiment title and export buffers returned by phyphox;
- connects the discovered endpoint to `PhyphoxReader`;
- requests `/control?cmd=start` after connecting.

If more than one phone is detected, EngiBench shows a detected-device selector rather than silently connecting to the wrong experiment.

## Large networks

A complete scan of a large campus or VPN subnet can involve many thousands of hosts. EngiBench bounds discovery work: normal small networks are scanned directly, while large networks are reduced to the `/24` neighborhood containing the computer.

This makes discovery practical, but it also means automatic discovery cannot be guaranteed on every enterprise, guest, VPN, or unusually segmented network.

## Automatic channel discovery

EngiBench first prefers buffers selected by the phyphox experiment author for export. If none are available, it falls back to declared experiment buffers. The result is fed into the same EngiBench telemetry pipeline as serial and simulated data.

## Architecture

```text
iPhone / Android
      |
      | phyphox Remote Access
      v
Local Network Scanner
      |
      +--> /config validation
      +--> experiment/channel discovery
      v
 PhyphoxReader
      |
      +--> /control?cmd=start
      +--> /get?... polling
      v
TelemetryController
      |
      +--> SampleBuffer --> plots / statistics / CSV export
      |
      +--> CSVRecorder
```

## Security

phyphox documents that Remote Access is not encrypted or password protected. Use it only on a trusted local network and do not expose the phone endpoint directly to the public internet.

## Troubleshooting

### No phone found

- Confirm a phyphox experiment is open.
- Confirm Remote Access is enabled.
- Confirm phone and computer are on the same local network.
- Avoid guest Wi-Fi networks that isolate clients from one another.
- Temporarily check host firewall rules if local-device traffic is blocked.
- VPNs can change routing and interface selection; disconnecting a VPN may help during testing.

### More than one phone found

Choose the intended experiment/device from **Detected phone**, then press Start again.

### Connected but no useful channels

Try another phyphox experiment. EngiBench automatically selects export buffers when available, but experiment configurations differ.

### Automatic discovery still does not work

Automatic scanning is best effort. Some managed networks block peer-to-peer traffic or use segmentation that prevents the computer from reaching the phone even when both appear to be on the same Wi-Fi.
