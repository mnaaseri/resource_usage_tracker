import psutil


class GetCPUInfo:
    """Get CPU usage for the system and individual processes."""

    def __init__(self, process_cache: dict | None = None) -> None:
        self._process_cache = process_cache if process_cache is not None else {}

    def _get_process(self, pid: int) -> psutil.Process | None:
        try:
            if pid not in self._process_cache:
                self._process_cache[pid] = psutil.Process(pid)
            process = self._process_cache[pid]
            if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
                return None
            return process
        except psutil.NoSuchProcess:
            self._process_cache.pop(pid, None)
            self._process_cache.pop(f"{pid}_cpu_primed", None)
            return None

    def get_process_cpu_usage(self, pid: int) -> dict | None:
        """Return process CPU usage as a percentage since the previous sample."""
        process = self._get_process(pid)
        if process is None:
            return None

        primed_key = f"{pid}_cpu_primed"
        if not self._process_cache.get(primed_key):
            process.cpu_percent(interval=None)
            self._process_cache[primed_key] = True
            return {"process_cpu_usage": 0.0}

        return {"process_cpu_usage": process.cpu_percent(interval=None)}

    def get_total_cpu_usage(self) -> dict:
        total_cpu_usage = psutil.cpu_percent()
        cpu_cores_usage = psutil.cpu_percent(percpu=True)

        return {
            "total_cpu_usage": total_cpu_usage,
            "cpu_cores_usage": cpu_cores_usage,
        }
