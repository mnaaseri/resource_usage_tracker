import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import logging 

from get_resources_info.get_cpu_info import GetCPUInfo
from get_resources_info.get_memory_info import GetMemoryInfo
from get_resources_info.get_storage_info import GetStorageInfo
from get_resources_info.get_process_info import GetProcessInfo

from utils.custom_exceptions import (GetResourceError,
                                     StreamlitRunError)

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

    def main_streamlit(self):
        """
        Main Function to generate streamlit charts.
        """
        st.title("Resource Usage in 2 Minutes Interval")

        total_memory_usage_chart_placeholder = st.empty()
        total_cpu_usage_chart_placeholder = st.empty()
        total_cpu_usage_table_placeholder = st.empty()
        storage_info_table_placeholder = st.empty()
        

        if self.pid:
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
            total_memory_usage = self.get_memory_info.get_total_memory_usage()
            
            try:
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
                        try:
                            memory_usage = self.get_memory_info.get_process_memory_usage(self.pid)
                            cpu_usage = self.get_cpu_info.get_process_cpu_usage(self.pid)

                            memory.loc[current_index, "Value"] = memory_usage["process_memory_usage"]
                            cpu.loc[current_index, "Value"] = cpu_usage["process_cpu_usage"]
                        except GetResourceError as e:
                            st.error(f"Error fetching memory or CPU usage {e}")
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
            except Exception as e:
                st.error(f"Error updating charts or tables: {e}")

if __name__ == "__main__":
    try:
        pid = sys.argv[1] if len(sys.argv) > 1 else None
        streamlit_app = StreamlitApp(pid)
        streamlit_app.main_streamlit()
    except StreamlitRunError as e:
        logger.error(f"Error initializing StreamlitApp: {e}")
