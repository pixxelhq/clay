from typing import Any


class SuccessfulExecutionException(Exception):
    """To be only used to communicate success codes/msgs
    by models to runner methods.
    """

    def __init__(self, message: Any) -> None:
        super().__init__(message)
        self.err_code = 0
        self.msg = message


class FailedExecutionException(Exception):
    """To be only used to communicate failure codes/msgs
    by models to runner methods.
    """

    def __init__(self, message: Any) -> None:
        super().__init__(message)
        self.err_code = 1
        self.msg = message
