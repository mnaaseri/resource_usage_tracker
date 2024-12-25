from configparser import ConfigParser
import os
from dotenv import load_dotenv
from get_resources_info.get_cpu_info import GetCPUInfo
from get_resources_info.get_memory_info import GetMemoryInfo
from get_resources_info.get_storage_info import GetStorageInfo
from notifier.send_email_notification import EmailSender
import logging

from utils.custom_exceptions import GetResourceError

load_dotenv()

logger = logging.getLogger(__name__)

# get_cpu_info        = GetCPUInfo()
# get_memory_info     = GetMemoryInfo()
get_storage_info    = GetStorageInfo()

sender_email    = os.getenv("SENDER_EMAIL")
password        = os.getenv("PASSWORD")
smtp_server     = os.getenv("SMTP_SERVER")
smtp_port       = os.getenv("SMTP_PORT")
receiver_email  = os.getenv("RECEIVER_EMAIL")

# email_sender = EmailSender(sender_email, receiver_email, smtp_server, smtp_port, password)

config = ConfigParser()
config.read("configs/config.conf")

process_cpu_threshold = config.get("PROCESS_ALERTS", "CPU_THRESHOLD")
process_memory_threshold = config.get("PROCESS_ALERTS", "MEMORY_THRESHOLD")

total_cpu_threshold = config.get("SYSTEM_ALERTS", "CPU_THRESHOLD")
total_memory_threshold = config.get("SYSTEM_ALERTS", "MEMORY_THRESHOLD")
total_storage_threshold = config.get("SYSTEM_ALERTS", "STORAGE_THRESHOLD")

class NotifierApp:
    def __init__(self, email_sender: EmailSender = None, memory_info: GetMemoryInfo = None, cpu_info: GetCPUInfo = None):
        self.email_sender = email_sender or EmailSender(sender_email, receiver_email, smtp_server, smtp_port, password)
        self.memory_info = memory_info or GetMemoryInfo()
        self.cpu_info = cpu_info or GetCPUInfo()

        
    def total_resource_usage(self):
        try:
            total_memory_usage = self.memory_info.get_total_memory_usage()
            total_cpu_usage = self.cpu_info.get_total_cpu_usage()

            if total_memory_usage["memory_percent"] > float(total_memory_threshold):
                self.email_sender.send_email(
                    subject="Memory Usage Alert",
                    body=f"""
                    Your total memory usage is {total_memory_usage["memory_percent"]},
                    which is more that your specified threshold.
                    """
                    )
                logger.info("An alert message had been sent to %s due to total memory usage", {receiver_email})

            if total_cpu_usage["total_cpu_usage"] > float(total_cpu_threshold):
                self.email_sender.send_email(
                    subject="CPU Usage Alert",
                    body=f"""
                    Your total cpu usage is {total_cpu_usage},
                    which is more that your specified threshold.
                    """
                    )
                logger.info("An alert message had been sent to %s due to total cpu usage", {receiver_email})
        except GetResourceError as e:
            logger.error("Error in Getting Resource usage: %s", e)

    def process_resource_usage(self, pid):
        try:
            process_memory_usage = self.memory_info.get_process_memory_usage(pid)
            process_cpu_usage = self.cpu_info.get_process_cpu_usage(pid)
            
            if process_cpu_usage["process_cpu_usage"] > float(process_cpu_threshold):
                self.email_sender.send_email(
                    subject="Process CPU Usage Alert",
                    body=f"""
                    Your process cpu usage is {process_cpu_usage},
                    which is more that your specified threshold."""
                    )
                logger.info("An alert message had been sent to %s due to process cpu usage", {receiver_email})
                

            if process_memory_usage["process_memory_usage"] > float(process_memory_threshold):
                self.email_sender.send_email(
                    subject="Process Memory Usage Alert",
                    body=f"""
                    Your process memory usage is {process_memory_usage},
                    which is more that your specified threshold."""
                    )
                logger.info("An alert message had been sent to %s due to process memory usage", {receiver_email})
        except GetResourceError as e:
            logger.error("Error in Getting Resource usage: %s", e)