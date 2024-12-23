import psutil

class GetStorageInfo():
    def __init__(self):
        pass

    def get_storage_info(self, path: str = "/") -> dict:
        usage = psutil.disk_usage(path)
        total_usage = usage.total / (1024 ** 3)
        used_space = usage.used / (1024 ** 3)
        free_space = usage.free / (1024 ** 3)
        usage_percent = usage.percent

        return {
            "total_usage": total_usage,
            "used_space": used_space,
            "free_space": free_space,
            "usage_percent": usage_percent, 
        }
