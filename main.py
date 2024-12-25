import argparse
import subprocess
import logging
import time
from configparser import ConfigParser
from apps.notifier_app import NotifierApp
from utils.custom_exceptions import(StreamlitRunError,
                                    NotifierRunError,
                                    ProcessRunError)
config = ConfigParser()
config.read("configs/config.conf")

logging.basicConfig(
    filename ='logging/log.txt',
    level=config.get("LOGGER", "LEVEL"))

logger = logging.getLogger(f"{__name__}")

notifier_app = NotifierApp()
alert_intervals = config.get("NOTIF_SETTING", "NOTIFICATION_INTERVAL")

def run_streamlit_app(streamlit_path: str, pid: str = None) -> None:
    """Run Streamlit app."""
    try:
        subprocess.Popen(
            ["streamlit", "run", streamlit_path, str(pid)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except StreamlitRunError as e:
        logger.error("Failed to run Streamlit app: %s", e)

def main(script_name: str) -> int:
    """Run a Python script and return its process ID."""
    try:
        process = subprocess.Popen(
            ["python", script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        logger.info("Process %s with pid %s started", script_name, process.pid)
        return process.pid
    except ProcessRunError as e:
        logger.error("Failed to start process: %s", e)
        return -1

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
        if pid != -1:
            run_streamlit_app("streamlit_app.py", pid)
            while True:
                try:
                    notifier_app.process_resource_usage(pid)
                    notifier_app.total_resource_usage()
                    time.sleep(int(alert_intervals) * 3600)
                except NotifierRunError as e:
                    logger.error("Error during resource usage processing: %s", e)
    else:
        run_streamlit_app("streamlit_app.py")
        while True:
            try:
                notifier_app.total_resource_usage()
                time.sleep(int(alert_intervals) * 3600)
            except NotifierRunError as e:
                logger.error("Error running notifier app: %s", e)
