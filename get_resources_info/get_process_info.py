import psutil
from datetime import datetime


class GetProcessInfo():
    def __init__(self) -> None:
        pass
     
    def check_for_children(self, pid: int) -> dict:
        process = psutil.Process(pid)
        children = process.children(recursive=True)
        children_info = {}
        if children:          
            for child in children:
                children_info[child.pid] = {"child_name": child.name,
                                            "child_status": child.status}
            return children_info
        else:
            return None
        
    def get_process_info(self, pid: int) -> dict:

        process = psutil.Process(pid)
        name = process.name()
        status = process.status()
        user_name = process.username()
        command = process.cmdline()
        open_files = process.open_files()
        start_time = datetime.fromtimestamp(process.create_time())
        up_time = datetime.now() - start_time

        proces_info = {
            "name": name,
            "status": status,
            "user_name": user_name,
            "command": command,
            "open_files": open_files,
            "start_time": start_time,
            "up_time": up_time.total_seconds()
        }

        return proces_info
