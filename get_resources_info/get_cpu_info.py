import psutil

class GetCPUInfo():
    """_summary_
    Get Cpu Usage.
    """
    def __init__(self) -> None:
        pass

    def get_process_cpu_usage(self, pid: int) -> dict:
        process = psutil.Process(pid)
        if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
            process_cpu_usage = process.cpu_percent(interval=1)

            return {
                "process_cpu_usage": process_cpu_usage
            }

    def get_total_cpu_usage(self) -> dict:
        total_cpu_usage = psutil.cpu_percent()
        cpu_cores_usage = psutil.cpu_percent(percpu=True)

        return {
            "total_cpu_usage": total_cpu_usage,
            "cpu_cores_usage": cpu_cores_usage}

        
        