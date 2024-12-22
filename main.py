import argparse
import subprocess
import logging
import time
from configparser import ConfigParser

from notifier_app import NotifierApp
from streamlit_app import StreamlitApp


config = ConfigParser()
config.read("configs/config.conf")

logging.basicConfig(
    filename = 'logging/log.txt',
                    level=config.get("LOGGER", "LEVEL"))
logger = logging.getLogger(f"{__name__}")

notifier_app = NotifierApp()

alert_intervals = config.get("NOTIF_SETTING", "NOTIFICATION_INTERVAL")

def run_streamlit_app(streamlit_path, pid=None):
    """_summary_
    Run Streamlit app.
    Args:
        script_path (_type_): str
        pid (_type_): str
    """
    subprocess.Popen(
        ["streamlit", "run", streamlit_path, str(pid)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def main(script_name):
    process = subprocess.Popen(
        ["python", script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    
    logger.info("Process %s with pid %s started", script_name, process.pid)
    return process.pid

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a Python script to track resource usage.")

    parser.add_argument(
        "-p", "--script",
        required=False, 
        help="The name or path of the Python script to run."
    )

    args = parser.parse_args()
    if args.script:
        pid = main(args.script)
        print(pid)
        run_streamlit_app("streamlit_app.py", pid)
        while True:
            notifier_app.process_resource_usage(pid)
            notifier_app.total_resource_usage()
            time.sleep(int(alert_intervals) * 3600)
    else:
        run_streamlit_app("streamlit_app.py")
        while True:
            notifier_app.total_resource_usage()
            time.sleep(int(alert_intervals) * 3600)
    
    