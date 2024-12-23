import psutil

class GetMemoryInfo():
    def __init__(self) -> None:
        pass

    def get_process_memory_usage(self, pid: int) -> dict:
        process = psutil.Process(pid)
        if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
            process_memory_usage = process.memory_info().rss / (1024 ** 2)  # Convert to MB

            return {
                "process_memory_usage": process_memory_usage
            }
    
    def get_total_memory_usage(self) -> dict:
        memory = psutil.virtual_memory()
        total_memory = memory.total / (1024 ** 3)
        used_memory = memory.used / (1024 ** 3)
        memory_percent = memory.percent
        
        return {
            "total_memory": total_memory,
            "used_memory": used_memory,
            "memory_percent": memory_percent,
            }


        