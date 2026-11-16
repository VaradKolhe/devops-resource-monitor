"""DevOps Resource Monitor Streamlit application."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import psutil
import streamlit as st

HISTORY_LIMIT = 1200


def _safe_metric(callable_: Any, default: Any = None) -> Any:
    """Return a metric, or None when the OS/API cannot provide it."""
    try:
        return callable_()
    except (OSError, PermissionError, NotImplementedError, ValueError, psutil.Error):
        return default


def collect_metrics() -> dict[str, Any]:
    """Collect current metrics visible to this process from the operating system."""
    cpu = _safe_metric(lambda: psutil.cpu_percent(interval=0.1))
    memory = _safe_metric(psutil.virtual_memory)
    disk = _safe_metric(lambda: psutil.disk_usage("/"))
    boot = _safe_metric(psutil.boot_time)
    return {
        "timestamp": datetime.now().astimezone(),
        "cpu_percent": float(cpu) if cpu is not None else None,
        "memory_percent": float(memory.percent) if memory is not None else None,
        "memory_available": int(memory.available) if memory is not None else None,
        "memory_total": int(memory.total) if memory is not None else None,
        "disk_percent": float(disk.percent) if disk is not None else None,
        "disk_free": int(disk.free) if disk is not None else None,
        "disk_total": int(disk.total) if disk is not None else None,
        "cpu_count": _safe_metric(psutil.cpu_count),
        "platform": _safe_metric(lambda: __import__("platform").platform()),
        "boot_time": datetime.fromtimestamp(boot).astimezone() if boot else None,
    }


def _format_bytes(value: int | None) -> str:
    if value is None:
        return "Unavailable"
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return "Unavailable"


def _metric_label(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "Unavailable"


def _record_sample(sample: dict[str, Any]) -> None:
    history = st.session_state.setdefault("history", [])
    history.append(sample)
    del history[:-HISTORY_LIMIT]


def _render_dashboard() -> None:
    sample = collect_metrics()
    _record_sample(sample)

    st.title("DevOps Resource Monitor")
    st.caption("Operating system metrics as visible to this application process.")

    control_col, status_col = st.columns([1, 4])
    with control_col:
        if st.button("↻ Refresh now", use_container_width=True):
            st.rerun()
    with status_col:
        refresh = st.selectbox("Automatic refresh", ["Off", "10 seconds", "30 seconds", "60 seconds"],
                               index=1, label_visibility="collapsed", key="refresh_interval")
        st.caption(f"Last collected: {sample['timestamp'].strftime('%Y-%m-%d %H:%M:%S %Z')}")

    cpu_col, mem_col, disk_col = st.columns(3)
    with cpu_col:
        st.metric("CPU utilization", _metric_label(sample["cpu_percent"]),
                  help="System-wide utilization reported by the operating system; in a container this may reflect the host.")
    with mem_col:
        st.metric("Memory utilization", _metric_label(sample["memory_percent"]),
                  help="Memory figures visible to this process; container limits may not be reflected on every platform.")
        st.caption(f"Available: {_format_bytes(sample['memory_available'])} of {_format_bytes(sample['memory_total'])}")
    with disk_col:
        st.metric("Root filesystem utilization", _metric_label(sample["disk_percent"]),
                  help="Usage of the filesystem mounted at / and visible to this process.")
        st.caption(f"Free: {_format_bytes(sample['disk_free'])} of {_format_bytes(sample['disk_total'])}")

    st.subheader("System information")
    info_cols = st.columns(3)
    info_cols[0].metric("Logical CPU cores", str(sample["cpu_count"] or "Unavailable"))
    info_cols[1].metric("Operating system", sample["platform"] or "Unavailable")
    uptime = "Unavailable"
    if sample["boot_time"]:
        elapsed = datetime.now().astimezone() - sample["boot_time"]
        uptime = f"{elapsed.days} days, {elapsed.seconds // 3600} hours"
    info_cols[2].metric("System uptime", uptime)

    st.subheader("Resource history")
    history = st.session_state.get("history", [])
    if len(history) < 2:
        st.info("History appears as readings accumulate during this session.")
    else:
        frame = pd.DataFrame(history)
        long_frame = frame.melt(id_vars="timestamp", value_vars=["cpu_percent", "memory_percent", "disk_percent"],
                                var_name="resource", value_name="utilization")
        long_frame["resource"] = long_frame["resource"].map({
            "cpu_percent": "CPU", "memory_percent": "Memory", "disk_percent": "Root filesystem"
        })
        fig = px.line(long_frame, x="timestamp", y="utilization", color="resource", markers=True,
                      labels={"timestamp": "Time", "utilization": "Utilization (%)", "resource": "Resource"},
                      title="Utilization over this session")
        fig.update_layout(legend_title_text="", hovermode="x unified", margin=dict(l=10, r=10, t=55, b=10))
        fig.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Showing {len(history)} readings. History is kept in this browser session (up to {HISTORY_LIMIT}).")

    st.caption("Metrics are not persisted. Container visibility depends on the host OS and runtime configuration.")


def main() -> None:
    st.set_page_config(page_title="DevOps Resource Monitor", page_icon="📊", layout="wide")
    refresh_seconds = {"Off": None, "10 seconds": 10, "30 seconds": 30, "60 seconds": 60}
    selected_refresh = st.session_state.get("refresh_interval", "10 seconds")
    if callable(getattr(st, "fragment", None)):
        @st.fragment(run_every=refresh_seconds.get(selected_refresh))
        def dashboard_fragment() -> None:
            _render_dashboard()

        dashboard_fragment()
    else:  # Older Streamlit versions still support history on rerun and manual refresh.
        _render_dashboard()


if __name__ == "__main__":
    main()
