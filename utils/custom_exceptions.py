class CustumError(Exception):
    """
    Base class for custum exceptions.
    """

class StreamlitRunError(CustumError):
    "Raise Error when stramlit can't run"

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class NotifierRunError(CustumError):
    "Raise Error when Notifier can't run"

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ProcessRunError(CustumError):
    "Raise Error when Notifier can't run"
    
    def __init__(self, *args: object) -> None:
        super().__init__(*args)