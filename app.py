from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from engibench.controller import TelemetryController
from engibench.export import samples_to_csv_bytes, samples_to_dataframe
from engibench.phone import PhoneBridgeError, PhyphoxReader
from engibench.serial_io import SerialReader, available_ports
from engibench.simulator import DemoSimulator
from engibench.statistics import channel_statistics, estimate_sample_rate

st.set_page_config(page_title="EngiBench OpenLab", page_icon="🔬", layout="wide")

PHONE_SOURCE = "Phone (iOS / Android)"


def initialize_session() -> None:
    """Create independent acquisition state for each browser session."""
    if "controller" not in st.session_state:
        st.session_state.controller = TelemetryController(max_samples=3000)
    if "source" not in st.session_state:
        st.session_state.source = None
    if "active_source_kind" not in st.session_state:
        st.session_state.active_source_kind = None
    if "active_source_config" not in st.session_state:
        st.session_state.active_source_config = None
    if "buffer_source_config" not in st.session_state:
        st.session_state.buffer_source_config = None
    if "source_notice" not in st.session_state:
        st.session_state.source_notice = ""
    if "recording_notice" not in st.session_state:
        st.session_state.recording_notice = ""


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
            st.error(f"Phone connection error: {current.last_error}")
        elif current.connected:
            title = current.experiment_title or "phyphox experiment"
            st.success(f"Acquisition: Phone connected through phyphox — {title}.")
        elif current.running:
            st.info(f"Connecting to phone at {current.base_url}...")
        else:
            st.warning("Phone source is not running.")

        if current.buffers:
            st.caption("Phone buffers: " + ", ".join(current.buffers))
        if current.measuring is False:
            st.warning("Phone is connected, but the phyphox experiment is paused.")
        if current.dropped_polls:
            st.warning(f"Phone polls with no usable values: {current.dropped_polls}")
        return

    if st.session_state.source_notice:
        st.info(st.session_state.source_notice)
    else:
        st.info(
            "Acquisition is stopped. Start the simulator, connect a serial board, "
            "or connect an iOS/Android phone."
        )


initialize_session()
ctl: TelemetryController = st.session_state.controller

st.title("EngiBench OpenLab")
st.caption(
    "Open-source telemetry workbench for embedded systems, electronics, sensors, and mechatronics."
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
    phone_url = ""
    phone_buffers_text = ""
    phone_interval = 0.25

    if source_kind == "Serial device":
        if not ports:
            st.warning("No serial ports detected. Connect a board, then refresh ports.")
        selected_port = st.selectbox("Serial port", ports if ports else ["No ports detected"])
        baud = st.selectbox("Baud rate", [9600, 19200, 38400, 57600, 115200], index=4)
        if st.button("Refresh ports", use_container_width=True):
            st.rerun()

    elif source_kind == PHONE_SOURCE:
        st.caption(
            "Uses phyphox Remote Access over the local network. "
            "The phone and this computer should normally be on the same Wi-Fi."
        )
        phone_url = st.text_input(
            "Phone Remote Access URL",
            placeholder="http://192.168.1.42:8080",
            help="Paste the exact address shown by phyphox after enabling Remote Access.",
        )
        phone_buffers_text = st.text_input(
            "Buffer names (optional)",
            placeholder="t,accX,accY,accZ",
            help="Leave empty to auto-discover buffers from the phyphox experiment.",
        )
        phone_interval = st.select_slider(
            "Phone poll interval",
            options=[0.1, 0.2, 0.25, 0.5, 1.0],
            value=0.25,
            format_func=lambda value: f"{value:g} s",
        )
        st.caption("Start the measurement in phyphox if EngiBench reports that it is paused.")

    manual_phone_buffers = tuple(
        name.strip() for name in phone_buffers_text.split(",") if name.strip()
    )

    if source_kind == "Demo simulator":
        requested_config = ("demo",)
    elif source_kind == "Serial device":
        requested_config = ("serial", selected_port, int(baud))
    else:
        requested_config = (
            "phone",
            phone_url.strip(),
            manual_phone_buffers,
            float(phone_interval),
        )

    active_config = st.session_state.active_source_config
    if st.session_state.source and active_config and active_config != requested_config:
        stop_active_source(
            "Acquisition stopped because the source settings changed. "
            "Buffer cleared to avoid mixing data.",
            clear_buffer=True,
        )

    running = source_is_running()
    serial_unavailable = source_kind == "Serial device" and not ports
    phone_unavailable = source_kind == PHONE_SOURCE and not phone_url.strip()
    source_unavailable = serial_unavailable or phone_unavailable

    col_start, col_stop = st.columns(2)
    start_label = "Restart" if running else "Start"
    start_clicked = col_start.button(
        start_label,
        use_container_width=True,
        disabled=source_unavailable,
    )
    stop_clicked = col_stop.button("Stop", use_container_width=True, disabled=not running)

    if start_clicked:
        if st.session_state.source:
            stop_active_source()
        previous_buffer_config = st.session_state.buffer_source_config
        if previous_buffer_config and previous_buffer_config != requested_config:
            ctl.buffer.clear()
        st.session_state.source_notice = ""

        current = None
        try:
            if source_kind == "Demo simulator":
                current = DemoSimulator(ctl.ingest)
            elif source_kind == "Serial device":
                current = SerialReader(str(selected_port), int(baud), ctl.ingest)
            else:
                current = PhyphoxReader(
                    phone_url,
                    ctl.ingest,
                    poll_interval=float(phone_interval),
                    buffers=manual_phone_buffers or None,
                )
        except PhoneBridgeError as exc:
            st.session_state.source_notice = f"Phone configuration error: {exc}"

        if current is not None:
            current.start()
            st.session_state.source = current
            st.session_state.active_source_kind = source_kind
            st.session_state.active_source_config = requested_config
            st.session_state.buffer_source_config = requested_config
        st.rerun()

    if stop_clicked:
        stop_active_source()
        st.rerun()

    if phone_unavailable:
        st.caption("Paste the phyphox Remote Access URL to enable Start.")

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
