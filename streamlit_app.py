import logging
import sys
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from get_resources_info.get_cpu_info import GetCPUInfo
from get_resources_info.get_memory_info import GetMemoryInfo
from get_resources_info.get_process_info import GetProcessInfo
from get_resources_info.get_storage_info import GetStorageInfo
from utils.custom_exceptions import GetResourceError, StreamlitRunError
from utils.process_manager import ProcessManager

logger = logging.getLogger(__name__)

CHART_WINDOW = timedelta(minutes=2)
REFRESH_INTERVAL_MS = 1000


def _normalize_pid(pid):
    if pid is None or pid == "None":
        return None
    return int(pid)


def _new_chart_df(interval_start: datetime) -> pd.DataFrame:
    time_range = pd.date_range(
        interval_start,
        interval_start + CHART_WINDOW,
        freq="s",
    )
    return pd.DataFrame({"Timestamp": time_range, "Value": [None] * len(time_range)})


def _init_chart_series(state_prefix: str) -> None:
    start_key = f"{state_prefix}_interval_start"
    if start_key not in st.session_state:
        st.session_state[start_key] = datetime.now()
    interval_start = st.session_state[start_key]
    st.session_state[f"{state_prefix}_memory"] = _new_chart_df(interval_start)
    st.session_state[f"{state_prefix}_cpu"] = _new_chart_df(interval_start)


def _maybe_roll_chart_window(state_prefix: str, current_time: datetime) -> None:
    start_key = f"{state_prefix}_interval_start"
    interval_start = st.session_state[start_key]
    if current_time >= interval_start + CHART_WINDOW:
        st.session_state[start_key] = current_time
        st.session_state[f"{state_prefix}_memory"] = _new_chart_df(current_time)
        st.session_state[f"{state_prefix}_cpu"] = _new_chart_df(current_time)


def _update_chart_point(state_prefix: str, current_time: datetime, memory_value, cpu_value) -> None:
    interval_start = st.session_state[f"{state_prefix}_interval_start"]
    current_index = int((current_time - interval_start).total_seconds())
    memory_df = st.session_state[f"{state_prefix}_memory"]
    cpu_df = st.session_state[f"{state_prefix}_cpu"]
    if current_index < len(memory_df):
        memory_df.loc[current_index, "Value"] = memory_value
        cpu_df.loc[current_index, "Value"] = cpu_value


class StreamlitApp:
    def __init__(self, pid=None):
        self.get_memory_info = GetMemoryInfo()
        self.get_storage_info = GetStorageInfo()
        self.get_process_info = GetProcessInfo()
        self.process_manager = ProcessManager()

        if "tracked_pid" not in st.session_state:
            st.session_state.tracked_pid = _normalize_pid(pid)
        if "psutil_process_cache" not in st.session_state:
            st.session_state.psutil_process_cache = {}

        self.get_cpu_info = GetCPUInfo(st.session_state.psutil_process_cache)

    def _get_kill_thresholds(self):
        memory_kill_threshold = float("inf")
        cpu_kill_threshold = float("inf")

        if st.session_state.tracked_pid is not None:
            kill_process = st.session_state.get("kill_process", "No")
            if kill_process == "Yes":
                memory_kill_threshold = st.session_state.get("memory", 80)
                cpu_kill_threshold = st.session_state.get("cpu", 80)

        return memory_kill_threshold, cpu_kill_threshold

    def _fetch_process_usage(self, pid: int) -> tuple[dict, dict] | None:
        memory_usage = self.get_memory_info.get_process_memory_usage(pid)
        cpu_usage = self.get_cpu_info.get_process_cpu_usage(pid)

        if not memory_usage or not cpu_usage:
            return None

        return memory_usage, cpu_usage

    def _check_and_kill_process(
        self,
        pid: int,
        memory_usage: dict,
        cpu_usage: dict,
        memory_kill_threshold: float,
        cpu_kill_threshold: float,
    ) -> bool:
        if (
            memory_usage["process_memory_usage"] > memory_kill_threshold
            or cpu_usage["process_cpu_usage"] > cpu_kill_threshold
        ):
            self.process_manager.kill_process(pid)
            st.session_state.tracked_pid = None
            st.session_state.process_killed_msg = True
            logger.info("Process %s terminated after exceeding thresholds.", pid)
            return False

        return True

    def _build_process_stats(self) -> pd.DataFrame:
        process_memory_df = st.session_state["process_memory"]
        process_cpu_df = st.session_state["process_cpu"]

        return pd.DataFrame(
            {
                "Metric": ["Max", "Avg"],
                "Process Memory Usage (MB)": [
                    process_memory_df["Value"].max(),
                    process_memory_df["Value"].mean(),
                ],
                "Process CPU Usage (%)": [
                    process_cpu_df["Value"].max(),
                    process_cpu_df["Value"].mean(),
                ],
            }
        )

    def _render_config_tab(self) -> None:
        st.write(
            "If you're running this app alongside a Python script, "
            "you can configure thresholds and terminate the process when they are exceeded."
        )

        if st.session_state.tracked_pid is not None:
            st.radio(
                "Do you want to kill the process after passing usage thresholds?",
                ["No", "Yes"],
                key="kill_process",
            )
            if st.session_state.kill_process == "Yes":
                st.slider(
                    "Memory threshold to kill the process (MB)",
                    0,
                    100,
                    value=80,
                    key="memory",
                )
                st.slider(
                    "CPU threshold to kill the process (%)",
                    0,
                    100,
                    value=80,
                    key="cpu",
                )

    def _collect_system_metrics(self) -> dict:
        total_memory_usage = self.get_memory_info.get_total_memory_usage()
        total_cpu_usage = self.get_cpu_info.get_total_cpu_usage()
        storage_info = self.get_storage_info.get_storage_info()

        per_cpu_dict = {
            f"cpu_{i}": cpu_percent
            for i, cpu_percent in enumerate(total_cpu_usage["cpu_cores_usage"])
        }
        total_cpu = pd.DataFrame({"CPU": ["Total"], "Total Usage": [total_cpu_usage["total_cpu_usage"]]})
        per_cpu_df = pd.DataFrame.from_dict(per_cpu_dict, orient="index", columns=["Usage"]).reset_index()
        per_cpu_df.columns = ["CPU", "Total Usage"]
        total_cpu = pd.concat([total_cpu, per_cpu_df], ignore_index=True)

        storage_info_df = pd.DataFrame(
            {
                " ": ["Total Usage", "Used Space", "Free Space", "Percent"],
                "GB": [
                    storage_info["total_usage"],
                    storage_info["used_space"],
                    storage_info["free_space"],
                    storage_info["usage_percent"],
                ],
            }
        )

        return {
            "total_memory_usage": total_memory_usage,
            "total_cpu": total_cpu,
            "storage_info_df": storage_info_df,
        }

    def _collect_process_metrics(self, pid: int) -> dict:
        process_info = self.get_process_info.get_process_info(pid)
        children_inf = self.get_process_info.check_for_children(pid)

        process_info_df = pd.DataFrame(
            {
                "Process": ["Process", "children"],
                "Info": [process_info, children_inf],
            }
        )

        return {
            "process_stats": self._build_process_stats(),
            "process_info_df": process_info_df,
        }

    def main_streamlit(self):
        """Render the dashboard and refresh metrics on a fixed interval."""
        if "system_interval_start" not in st.session_state:
            _init_chart_series("system")
        if st.session_state.tracked_pid is not None and "process_interval_start" not in st.session_state:
            _init_chart_series("process")

        tab1, tab2 = st.tabs(["charts", "configs"])

        with tab2:
            self._render_config_tab()

        st_autorefresh(interval=REFRESH_INTERVAL_MS, key="metrics_refresh")

        if st.session_state.pop("process_killed_msg", False):
            st.success("Process has been terminated!")

        current_time = datetime.now()
        _maybe_roll_chart_window("system", current_time)
        if st.session_state.tracked_pid is not None:
            _maybe_roll_chart_window("process", current_time)

        memory_kill_threshold, cpu_kill_threshold = self._get_kill_thresholds()
        pid = st.session_state.tracked_pid

        try:
            system_metrics = self._collect_system_metrics()
            _update_chart_point(
                "system",
                current_time,
                system_metrics["total_memory_usage"]["used_memory"],
                system_metrics["total_cpu"]["Total Usage"].iloc[0],
            )
        except GetResourceError as e:
            st.error(f"Error fetching system resource usage: {e}")
            system_metrics = None

        process_metrics = None
        if pid is not None:
            try:
                process_usage = self._fetch_process_usage(pid)
                if process_usage is None:
                    logger.warning("Process %s not found or stopped.", pid)
                    st.session_state.tracked_pid = None
                else:
                    memory_usage, cpu_usage = process_usage

                    if memory_kill_threshold != float("inf") or cpu_kill_threshold != float("inf"):
                        if not self._check_and_kill_process(
                            pid,
                            memory_usage,
                            cpu_usage,
                            memory_kill_threshold,
                            cpu_kill_threshold,
                        ):
                            pid = None

                    if pid is not None:
                        _update_chart_point(
                            "process",
                            current_time,
                            memory_usage["process_memory_usage"],
                            cpu_usage["process_cpu_usage"],
                        )
                        process_metrics = self._collect_process_metrics(pid)
            except GetResourceError as e:
                st.error(f"Error fetching process resource usage: {e}")
                st.session_state.tracked_pid = None

        with tab1:
            if system_metrics:
                st.subheader("Storage_info")
                st.table(system_metrics["storage_info_df"])

                st.subheader("Total Memory Stat")
                st.line_chart(st.session_state["system_memory"].set_index("Timestamp"))

                st.subheader("Total CPU Stat")
                st.line_chart(st.session_state["system_cpu"].set_index("Timestamp"))
                st.table(system_metrics["total_cpu"])

            if process_metrics:
                st.subheader("Process Info")
                st.table(process_metrics["process_info_df"])

                st.subheader("Process Usage Stat")
                st.table(process_metrics["process_stats"])

                st.subheader("Process Memory Usage")
                st.line_chart(st.session_state["process_memory"].set_index("Timestamp"))

                st.subheader("Process CPU Usage")
                st.line_chart(st.session_state["process_cpu"].set_index("Timestamp"))


if __name__ == "__main__":
    try:
        pid = sys.argv[1] if len(sys.argv) > 1 else None
        streamlit_app = StreamlitApp(pid)
        streamlit_app.main_streamlit()
    except StreamlitRunError as e:
        logger.error("Error initializing StreamlitApp: %s", e)
