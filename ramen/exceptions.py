from typing import Any


class SuccessfulExecutionException(Exception):
    """To be only used to communicate success codes/msgs
    by models to runner methods.
    """

    def __init__(
        self, message: Any, data: Any = None, http_status_code: int = 200
    ) -> None:
        super().__init__(message)
        self.msg = message
        self.data = data
        self.http_status_code = http_status_code


class FailedExecutionException(Exception):
    """To be only used to communicate failure codes/msgs
    by models to runner methods.
    """

    def __init__(self, message: Any, logs: Any = "", http_status_code: int = 500) -> None:
        super().__init__(message)
        self.msg = message
        self.logs = logs
        self.http_status_code = http_status_code
