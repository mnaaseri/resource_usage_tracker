import psutil
import logging
import os
import signal


class ProcessManager:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def kill_process(self, pid:int) -> None:
        """ Kill Process with having pid
        Args:
            pid (int)
        """
        try:
            process = psutil.Process(pid)
            process.terminate()
            process.wait()
            self.logger.info("Process %s has been terminated.", pid)
        except psutil.NoSuchProcess:
            self.logger.error("Process with PID %s does not exist.", pid)
        except psutil.AccessDenied:
            self.logger.error("You do not have permission to terminate this process.")
        except Exception as e:
            self.logger(f"Couldn't kill the process Due to {e}")
# # import psutil

# class ProcessManager:
#     @staticmethod
#     def kill_process(pid):
#         try:
#             process = psutil.Process(pid)
#             for child in process.children(recursive=True):
#                 child.terminate()
#                 child.wait(timeout=5)
#             process.terminate()
#             process.wait(timeout=5)
#         except psutil.NoSuchProcess:
#             pass
#         except Exception as e:
#             raise Exception(f"Error killing process {pid}: {e}")
