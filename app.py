from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from engibench.controller import TelemetryController
from engibench.export import samples_to_csv_bytes, samples_to_dataframe
from engibench.serial_io import SerialReader, available_ports
from engibench.simulator import DemoSimulator
from engibench.statistics import channel_statistics, estimate_sample_rate

st.set_page_config(page_title="EngiBench OpenLab", page_icon="🔬", layout="wide")


@st.cache_resource
def controller() -> TelemetryController:
    return TelemetryController(max_samples=3000)


ctl = controller()

if "source" not in st.session_state:
    st.session_state.source = None
if "source_error" not in st.session_state:
    st.session_state.source_error = ""

st.title("EngiBench OpenLab")
st.caption("Open-source telemetry workbench for embedded systems, electronics, sensors, and mechatronics.")

with st.sidebar:
    st.header("Acquisition")
    source_kind = st.radio("Data source", ["Demo simulator", "Serial device"])
    ports = available_ports()
    selected_port = None
    baud = 115200
    if source_kind == "Serial device":
        selected_port = st.selectbox("Serial port", ports if ports else ["No ports detected"])
        baud = st.selectbox("Baud rate", [9600, 19200, 38400, 57600, 115200], index=4)

    col_start, col_stop = st.columns(2)
    if col_start.button("Start", use_container_width=True):
        current = st.session_state.source
        if current:
            current.stop()
        st.session_state.source_error = ""
        if source_kind == "Demo simulator":
            current = DemoSimulator(ctl.ingest)
        elif selected_port and selected_port != "No ports detected":
            current = SerialReader(
                selected_port,
                int(baud),
                ctl.ingest,
                error_callback=lambda message: setattr(st.session_state, "source_error", message),
            )
        else:
            current = None
            st.session_state.source_error = "No serial port is available."
        if current:
            current.start()
        st.session_state.source = current

    if col_stop.button("Stop", use_container_width=True):
        current = st.session_state.source
        if current:
            current.stop()
        st.session_state.source = None

    if st.button("Clear buffer", use_container_width=True):
        ctl.buffer.clear()

    st.divider()
    st.header("Recording")
    if not ctl.recording:
        if st.button("Start CSV recording", use_container_width=True):
            try:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                ctl.start_recording(Path("recordings") / f"engibench-{stamp}.csv")
                st.success("Recording started")
            except ValueError as exc:
                st.warning(str(exc))
    else:
        st.success("Recording active")
        if st.button("Stop recording", use_container_width=True):
            ctl.stop_recording()

if st.session_state.source_error:
    st.error(st.session_state.source_error)


@st.fragment(run_every=0.5)
def live_dashboard() -> None:
    samples = ctl.buffer.snapshot()
    if not samples:
        st.info("Start the demo simulator or connect a serial device to begin.")
        return

    frame = samples_to_dataframe(samples)
    stats = channel_statistics(samples)
    sample_rate = estimate_sample_rate(samples)

    top1, top2, top3 = st.columns(3)
    top1.metric("Buffered samples", len(samples))
    top2.metric("Channels", len(stats))
    top3.metric("Estimated sample rate", f"{sample_rate:.2f} Hz" if sample_rate else "—")

    st.subheader("Live signals")
    value_columns = [column for column in frame.columns if column not in {"timestamp", "source"}]
    chart_frame = frame[["timestamp", *value_columns]].set_index("timestamp")
    st.line_chart(chart_frame, height=360)

    st.subheader("Channel statistics")
    stat_rows = [{"channel": channel, **values} for channel, values in stats.items()]
    st.dataframe(stat_rows, use_container_width=True, hide_index=True)

    st.subheader("Recent telemetry")
    st.dataframe(frame.tail(50), use_container_width=True, hide_index=True)

    st.download_button(
        "Download current buffer as CSV",
        data=samples_to_csv_bytes(samples),
        file_name="engibench-buffer.csv",
        mime="text/csv",
        use_container_width=True,
    )


live_dashboard()
