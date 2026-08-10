from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from engibench.controller import TelemetryController
from engibench.export import samples_to_csv_bytes, samples_to_dataframe
from engibench.phone import PhyphoxReader
from engibench.phone_discovery import DiscoveredPhone, discover_phyphox_phones
from engibench.serial_io import SerialReader, available_ports
from engibench.simulator import DemoSimulator
from engibench.statistics import channel_statistics, estimate_sample_rate

st.set_page_config(page_title="EngiBench OpenLab", page_icon="🔬", layout="wide")

PHONE_SOURCE = "Phone (iOS / Android)"


def initialize_session() -> None:
    """Create independent acquisition state for each browser session."""
    defaults = {
        "controller": TelemetryController(max_samples=3000),
        "source": None,
        "active_source_kind": None,
        "active_source_config": None,
        "buffer_source_config": None,
        "source_notice": "",
        "recording_notice": "",
        "discovered_phones": [],
        "phone_discovery_error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def stop_active_source(
    message: str = "Acquisition stopped.",
    *,
    clear_buffer: bool = False,
) -> None:
    """Stop acquisition and recording together so UI state cannot become stale."""
    current = st.session_state.source
    if current:
        current.stop()
    ctl = st.session_state.controller
    if ctl.recording:
        ctl.stop_recording()
        st.session_state.recording_notice = "Recording stopped with acquisition."
    if clear_buffer:
        ctl.buffer.clear()
        st.session_state.buffer_source_config = None
    st.session_state.source = None
    st.session_state.active_source_kind = None
    st.session_state.active_source_config = None
    st.session_state.source_notice = message


def source_is_running() -> bool:
    current = st.session_state.source
    return bool(current and current.running)


def render_source_status() -> None:
    current = st.session_state.source
    if isinstance(current, DemoSimulator):
        if current.running:
            st.success(
                "Acquisition: Demo simulator is running. "
                "Values are simulated, not hardware measurements."
            )
        else:
            st.warning("Demo simulator is stopped.")
        return

    if isinstance(current, SerialReader):
        if current.last_error:
            st.error(f"Serial error on {current.port}: {current.last_error}")
        elif current.connected:
            st.success(f"Acquisition: Serial {current.port} at {current.baudrate} baud.")
        elif current.running:
            st.info(f"Connecting to {current.port} at {current.baudrate} baud...")
        else:
            st.warning(f"Serial source {current.port} is not running.")
        if current.dropped_lines:
            st.warning(f"Ignored telemetry lines: {current.dropped_lines}")
        return

    if isinstance(current, PhyphoxReader):
        if current.last_error:
            st.error(current.last_error)
        elif current.connected:
            title = current.experiment_title or "phyphox experiment"
            st.success(f"Phone connected automatically: {title} · {current.base_url}")
            if current.buffers:
                st.caption("Detected channels: " + ", ".join(current.buffers))
            if current.measuring is False:
                st.warning("Phone is connected, but phyphox reports that measurement is paused.")
        elif current.running:
            st.info("Connecting to the detected phone...")
        else:
            st.warning("Phone source is not running.")
        if current.dropped_polls:
            st.caption(f"Phone polls without usable values: {current.dropped_polls}")
        return

    if st.session_state.source_notice:
        st.info(st.session_state.source_notice)
    else:
        st.info("Acquisition is stopped. Choose a source and press Start.")


def auto_detect_phone() -> DiscoveredPhone | None:
    """Scan the local network and return a single unambiguous phyphox phone."""
    st.session_state.phone_discovery_error = ""
    with st.spinner("Looking for iOS / Android phones with phyphox Remote Access..."):
        try:
            phones = discover_phyphox_phones()
        except Exception as exc:
            st.session_state.discovered_phones = []
            st.session_state.phone_discovery_error = str(exc)
            return None
    st.session_state.discovered_phones = phones
    if not phones:
        st.session_state.phone_discovery_error = (
            "No phone found. Open a phyphox experiment on the phone, enable Remote Access, "
            "and keep the phone and computer on the same local Wi-Fi."
        )
        return None
    if len(phones) > 1:
        st.session_state.phone_discovery_error = (
            f"Found {len(phones)} phones. Select one from the detected-device list."
        )
        return None
    return phones[0]


initialize_session()
ctl: TelemetryController = st.session_state.controller

st.title("EngiBench OpenLab")
st.caption(
    "Open-source telemetry workbench for embedded systems, electronics, phone sensors, and mechatronics."
)

with st.sidebar:
    st.header("Acquisition")
    source_kind = st.radio(
        "Data source",
        ["Demo simulator", "Serial device", PHONE_SOURCE],
        key="selected_source_kind",
    )

    ports = available_ports()
    selected_port = None
    baud = 115200
    selected_phone: DiscoveredPhone | None = None

    if source_kind == "Serial device":
        if not ports:
            st.warning("No serial ports detected. Connect a board, then refresh ports.")
        selected_port = st.selectbox("Serial port", ports if ports else ["No ports detected"])
        baud = st.selectbox("Baud rate", [9600, 19200, 38400, 57600, 115200], index=4)
        if st.button("Refresh ports", use_container_width=True):
            st.rerun()

    elif source_kind == PHONE_SOURCE:
        st.caption(
            "No URL or buffer names needed. EngiBench scans the local network for phyphox "
            "Remote Access and detects the experiment channels automatically."
        )
        phones: list[DiscoveredPhone] = st.session_state.discovered_phones
        if phones:
            labels = [f"{phone.title} · {phone.base_url}" for phone in phones]
            selected_label = st.selectbox("Detected phone", labels)
            selected_phone = phones[labels.index(selected_label)]
        if st.session_state.phone_discovery_error:
            st.warning(st.session_state.phone_discovery_error)
        st.caption("On the phone: open phyphox → choose an experiment → enable Remote Access.")

    if source_kind == "Demo simulator":
        requested_config = (source_kind,)
    elif source_kind == "Serial device":
        requested_config = (source_kind, selected_port, int(baud))
    else:
        requested_config = (
            source_kind,
            selected_phone.base_url if selected_phone else None,
        )

    active_config = st.session_state.active_source_config
    if st.session_state.source and active_config and active_config != requested_config:
        stop_active_source(
            "Acquisition stopped because the source settings changed. Buffer cleared to avoid mixing data.",
            clear_buffer=True,
        )

    running = source_is_running()
    serial_unavailable = source_kind == "Serial device" and not ports
    col_start, col_stop = st.columns(2)
    start_label = "Restart" if running else ("Auto Detect & Start" if source_kind == PHONE_SOURCE else "Start")
    start_clicked = col_start.button(
        start_label,
        use_container_width=True,
        disabled=serial_unavailable,
    )
    stop_clicked = col_stop.button("Stop", use_container_width=True, disabled=not running)

    if start_clicked:
        if st.session_state.source:
            stop_active_source()

        if source_kind == PHONE_SOURCE:
            phone = selected_phone or auto_detect_phone()
            if phone is None and len(st.session_state.discovered_phones) == 1:
                phone = st.session_state.discovered_phones[0]
            if phone is None:
                st.rerun()
            requested_config = (PHONE_SOURCE, phone.base_url)
            current = PhyphoxReader(phone.base_url, ctl.ingest, buffers=phone.buffers or None)
        elif source_kind == "Demo simulator":
            current = DemoSimulator(ctl.ingest)
        else:
            current = SerialReader(str(selected_port), int(baud), ctl.ingest)

        previous_buffer_config = st.session_state.buffer_source_config
        if previous_buffer_config and previous_buffer_config != requested_config:
            ctl.buffer.clear()
        st.session_state.source_notice = ""
        current.start()
        st.session_state.source = current
        st.session_state.active_source_kind = source_kind
        st.session_state.active_source_config = requested_config
        st.session_state.buffer_source_config = requested_config
        st.rerun()

    if stop_clicked:
        stop_active_source()
        st.rerun()

    if source_kind == PHONE_SOURCE and st.button("Scan again", use_container_width=True):
        if st.session_state.source:
            stop_active_source(clear_buffer=True)
        st.session_state.discovered_phones = []
        auto_detect_phone()
        st.rerun()

    clear_disabled = ctl.recording
    if st.button("Clear buffer", use_container_width=True, disabled=clear_disabled):
        ctl.buffer.clear()
        st.session_state.buffer_source_config = (
            st.session_state.active_source_config if source_is_running() else None
        )
        st.session_state.source_notice = "Telemetry buffer cleared."
        st.rerun()
    if clear_disabled:
        st.caption("Stop recording before clearing the buffer.")

    st.divider()
    st.header("Recording")
    if ctl.recording:
        st.success("Recording active")
        if ctl.recording_path:
            st.caption(f"File: {ctl.recording_path}")
        if st.button("Stop recording", use_container_width=True):
            ctl.stop_recording()
            st.session_state.recording_notice = "Recording stopped."
            st.rerun()
    else:
        if st.session_state.recording_notice:
            st.caption(st.session_state.recording_notice)
        if ctl.last_recording_path:
            st.caption(f"Last file: {ctl.last_recording_path}")
        can_record = source_is_running() and len(ctl.buffer) > 0
        if st.button("Start CSV recording", use_container_width=True, disabled=not can_record):
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            ctl.start_recording(Path("recordings") / f"engibench-{stamp}.csv")
            st.session_state.recording_notice = ""
            st.rerun()
        if not can_record:
            st.caption("Start acquisition and wait for a sample before recording.")


@st.fragment(run_every=0.5)
def live_dashboard() -> None:
    current = st.session_state.source
    if ctl.recording and current is not None and not current.running:
        ctl.stop_recording()
        st.session_state.recording_notice = (
            "Recording stopped automatically because acquisition ended."
        )
    render_source_status()
    if st.session_state.recording_notice:
        st.caption(st.session_state.recording_notice)
    samples = ctl.buffer.snapshot()
    if not samples:
        st.info("No telemetry buffered yet.")
        return

    frame = samples_to_dataframe(samples)
    stats = channel_statistics(samples)
    sample_rate = estimate_sample_rate(samples[-200:])

    top1, top2, top3 = st.columns(3)
    top1.metric("Buffered samples", len(samples))
    top2.metric("Channels", len(stats))
    top3.metric("Estimated sample rate", f"{sample_rate:.2f} Hz" if sample_rate else "—")

    st.subheader("Live signals")
    value_columns = [column for column in frame.columns if column not in {"timestamp", "source"}]
    chart_frame = frame[["timestamp", *value_columns]].copy()
    chart_frame["elapsed_s"] = chart_frame["timestamp"] - chart_frame["timestamp"].iloc[0]
    chart_frame = chart_frame.drop(columns="timestamp").set_index("elapsed_s")
    st.line_chart(chart_frame, height=360)
    st.caption("X-axis: elapsed seconds since the first buffered sample.")

    st.subheader("Channel statistics")
    stat_rows = []
    for channel, values in stats.items():
        rounded = {name: round(value, 5) for name, value in values.items()}
        stat_rows.append({"channel": channel, **rounded})
    st.dataframe(stat_rows, use_container_width=True, hide_index=True)

    st.subheader("Recent telemetry")
    display_frame = frame.tail(50).copy()
    display_frame["timestamp"] = display_frame["timestamp"].map(
        lambda value: datetime.fromtimestamp(value, tz=timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        + " UTC"
    )
    st.dataframe(display_frame, use_container_width=True, hide_index=True)

    st.download_button(
        "Download current buffer as CSV",
        data=samples_to_csv_bytes(samples),
        file_name="engibench-buffer.csv",
        mime="text/csv",
        use_container_width=True,
    )


live_dashboard()
