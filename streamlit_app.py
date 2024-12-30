import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

from get_resources_info.get_cpu_info import GetCPUInfo
from get_resources_info.get_memory_info import GetMemoryInfo
from get_resources_info.get_process_info import GetProcessInfo
from get_resources_info.get_storage_info import GetStorageInfo
from utils.custom_exceptions import GetResourceError, StreamlitRunError
from utils.process_manager import ProcessManager

logger = logging.getLogger(__name__)

class StreamlitApp():
    def __init__(self, pid=None):
        if pid != "None":
            self.pid = int(pid)
        else:
            self.pid = pid

        self.get_cpu_info = GetCPUInfo()
        self.get_memory_info = GetMemoryInfo()
        self.get_storage_info = GetStorageInfo()
        self.get_process_info = GetProcessInfo()
        self.process_manager = ProcessManager()

        self.tab1, self.tab2 = st.tabs(["charts", "configs"])
        self.monitor_thread = True
        
    def monitor_process(self, pid, memory_kill_threshold, cpu_kill_threshold):
        add_script_run_ctx(threading.current_thread())

        while pid != "None":
            try:
                memory_usage = self.get_memory_info.get_process_memory_usage(pid)
                cpu_usage = self.get_cpu_info.get_process_cpu_usage(pid)
                logger.info("threshold %s", memory_kill_threshold)
                if not memory_usage or not cpu_usage:
                    logger.warning(f"Process {pid} not found or stopped.")
                    pid = "None"
                    self.pid = "None"
                    break

                if memory_usage["process_memory_usage"] > memory_kill_threshold or \
                cpu_usage["process_cpu_usage"] > cpu_kill_threshold:
                    self.process_manager.kill_process(pid)
                    os.waitpid(pid, 0)
                    
                    logger.info("Process terminated.")
                    pid = "None"
                    self.pid = "None"
                    st.session_state["monitor_status"] = "Updated status"
                    st.success("Process has been terminated!")
                    time.sleep(1)
                    break
    
            except GetResourceError as e:
                st.error(f"Error fetching resources for PID {pid}: {e}")
                pid = "None"
                self.pid = "None"
                break

            except OSError as e:
                st.error(f"Error cleaning up process {pid}: {e}")
                pid = "None"
                self.pid = "None"
                break
            
            time.sleep(1)

        logger.info("Monitoring stopped. Ready for new processes.")
        st.info("Monitoring process completed. Awaiting further actions.")
        time.sleep(5)

    def main_streamlit(self):
        """
        Main Function to generate streamlit charts.
        """
        memory_kill_threshold = float('inf')
        cpu_kill_threshold = float('inf')

        with self.tab1:
            total_memory_usage_chart_placeholder = st.empty()
            total_cpu_usage_chart_placeholder = st.empty()
            total_cpu_usage_table_placeholder = st.empty()
            storage_info_table_placeholder = st.empty()
        
        with self.tab2:
            st.write("If you're running this app along side a python script, you can config and terminate the process after passing a threshold")
            
        if self.pid != "None":
            with self.tab2:
                kill_process = st.radio(
                    "Do you want to kill the process after passing usage thresholds?",
                    ["No", "Yes"], key="kill_process")
                if kill_process =="Yes":
                    memory_kill_threshold = st.slider("Memory threshold to kill the process", 0, 100, value=80, key="memory")
                    cpu_kill_threshold = st.slider("CPU threshold to kill the process", 0, 100, value=80, key="cpu")

            with self.tab1:
                process_memory_chart_placeholder = st.empty()
                process_cpu_chart_placeholder = st.empty()
                process_info_table_placeholder = st.empty()
                process_usage_table_placeholder = st.empty()

        interval_duration = timedelta(minutes=2)
        interval_start_time = datetime.now()

        time_range = pd.date_range(
            interval_start_time,
            interval_start_time + interval_duration,
            freq="s")

        memory = pd.DataFrame({"Timestamp": time_range, "Value": [None] * len(time_range)})
        cpu = pd.DataFrame({"Timestamp": time_range, "Value": [None] * len(time_range)})
        if not hasattr(self, "monitor_thread_started"):
            self.monitor_thread = threading.Thread(
                target=self.monitor_process,
                args=(self.pid, memory_kill_threshold, cpu_kill_threshold),
            )
            self.monitor_thread.daemon = True
            st.write("Creating monitoring thread for PID %s", self.pid)
            if self.monitor_thread.is_alive():
                st.write("Monitor thread already running.")
            else:
                st.write("Starting monitoring thread.")
                self.monitor_thread.start()

                self.monitor_thread_started = True

        while True:
            current_time = datetime.now()
            if current_time >= interval_start_time + interval_duration:
                interval_start_time = datetime.now()
                time_range = pd.date_range(
                    interval_start_time,
                    interval_start_time + interval_duration,
                    freq="s"
                    )
                memory = pd.DataFrame({"Timestamp": time_range, "Value": [None] * len(time_range)})
                cpu = pd.DataFrame({"Timestamp": time_range, "Value": [None] * len(time_range)})
            
            current_index = int((current_time - interval_start_time).total_seconds())

            if current_index < len(memory):
                try: 
                    memory_usage = self.get_memory_info.get_total_memory_usage()
                    cpu_usage = self.get_cpu_info.get_total_cpu_usage()

                    memory.loc[current_index, "Value"] = memory_usage["used_memory"]
                    cpu.loc[current_index, "Value"] = cpu_usage["total_cpu_usage"]
                except GetResourceError as e:
                    st.error(f"Error fetching memory or CPU usage {e}")                    

            try:
                total_memory_usage = self.get_memory_info.get_total_memory_usage()
                total_stat_memory = pd.DataFrame({
                    "Usage": ["Total Memory", "Total Used Memory", "Used Memory Percent"],
                    "Total Memory Usage": [
                        total_memory_usage["total_memory"],
                        total_memory_usage["used_memory"],
                        total_memory_usage["memory_percent"]]
                    })
                
                total_cpu_usage = self.get_cpu_info.get_total_cpu_usage()
                all_cpu = total_cpu_usage["total_cpu_usage"]
                per_cpu = total_cpu_usage["cpu_cores_usage"]

                per_cpu_dict = {}
                for i, cpu_percent in enumerate(per_cpu):
                    cpu_no = f"cpu_{i}"
                    per_cpu_dict[cpu_no] = cpu_percent
                    
                total_cpu = pd.DataFrame({
                    "CPU": ["Total"],
                    "Total Usage": [all_cpu]
                })
                per_cpu_df = pd.DataFrame.from_dict(
                    per_cpu_dict, orient='index',
                    columns=["Usage"]).reset_index()
                per_cpu_df.columns = ["CPU", "Total Usage"]

                total_cpu = pd.concat([total_cpu, per_cpu_df], ignore_index=True)

                storage_info = self.get_storage_info.get_storage_info()

                storage_info_df = pd.DataFrame({
                    " " : ["Total Usage", "Used Space",
                        "Free Space", "Percent"],
                    "GB": [storage_info['total_usage'],
                        storage_info['used_space'],
                        storage_info['free_space'],
                        storage_info['usage_percent']],
                })

            except Exception as e:
                st.error(f"Error updating charts or tables: {e}")
            
            with self.tab1:
                with storage_info_table_placeholder.container():
                    st.subheader("Storage_info")
                    st.table(storage_info_df)
                with total_memory_usage_chart_placeholder.container():
                    st.subheader("Total Memory Stat")
                    st.line_chart(memory.set_index("Timestamp"))
                with total_cpu_usage_chart_placeholder.container():
                    st.subheader("Total CPU Stat")
                    st.line_chart(cpu.set_index("Timestamp"))
                with total_cpu_usage_table_placeholder.container():
                    st.subheader("Total CPU Stat")
                    st.table(total_cpu)

            if self.pid != "None":

                if current_time >= interval_start_time + interval_duration:
                    interval_start_time = datetime.now()
                    time_range = pd.date_range(
                        interval_start_time,
                        interval_start_time + interval_duration,
                        freq="s"
                        )

                    memory = pd.DataFrame({"Timestamp": time_range,
                                        "Value": [None] * len(time_range)})
                    cpu = pd.DataFrame({"Timestamp": time_range,
                                        "Value": [None] * len(time_range)})
                    
                current_index = int((current_time - interval_start_time).total_seconds())
                
                if current_index < len(memory):
                    
                    if self.pid != "None":
                        memory_usage = self.get_memory_info.get_process_memory_usage(self.pid)
                        cpu_usage = self.get_cpu_info.get_process_cpu_usage(self.pid)
                    else:
                        break
                    memory.loc[current_index, "Value"] = memory_usage["process_memory_usage"]
 
                process_stats = pd.DataFrame({
                    "Metric": ["Max", "Avg"],
                    "Process Memory Usage": [
                        memory["Value"].max(),
                        memory["Value"].mean()
                    ],
                    "Process CPU Usage": [
                        cpu["Value"].max(),
                        cpu["Value"].mean()
                    ]
                })
                process_info = self.get_process_info.get_process_info(self.pid)
                children_inf = self.get_process_info.check_for_children(self.pid)

                process_info_df = pd.DataFrame({
                    "Process": ["Process", "children"],
                    "Info": [process_info, children_inf]
                })
                    
                with self.tab1:
                    with process_info_table_placeholder.container():
                        st.subheader("Process Info")
                        st.table(process_info_df)
                with process_usage_table_placeholder.container():
                    st.subheader("Process Usage Stat")
                    st.table(process_stats)
                with process_memory_chart_placeholder.container():
                    st.subheader("Process Memory Usage")
                    st.line_chart(memory.set_index("Timestamp"))
                with process_cpu_chart_placeholder.container():
                    st.subheader("Process CPU Usage")
                    st.line_chart(cpu.set_index("Timestamp"))
                
                logger.info("memory kill threshold, %s", memory_kill_threshold)
                st.write("memory kill threshold, %s", memory_kill_threshold)
                st.write(f"Thread alive: {self.monitor_thread.is_alive()}")
                
if __name__ == "__main__":
    try:
        pid = sys.argv[1] if len(sys.argv) > 1 else None
        streamlit_app = StreamlitApp(pid)
        streamlit_app.main_streamlit()
    except StreamlitRunError as e:
        logger.error(f"Error initializing StreamlitApp: {e}")
