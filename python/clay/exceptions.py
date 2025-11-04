from typing import Any


class FailedExecutionException(Exception):
    """To be only used to communicate failure codes/msgs
    by models to runner methods.
    """

    def __init__(
        self,
        message: Any,
        http_status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.msg = message
        self.http_status_code = http_status_code

class OutputOverwriteException(Exception):
    """To be raised when a model is trying to overwrite an output

    Args:
        Exception (_type_): _description_
    """

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class UnknownFormatException(Exception):
    def __init__(self, format: str) -> None:
        super().__init__(f"{format} is an unknown exception type")
