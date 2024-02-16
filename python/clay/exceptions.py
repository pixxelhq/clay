from typing import Any, Optional

from clay import types


class SuccessfulExecutionException(Exception):
    """To be only used to communicate success codes/msgs
    by models to runner methods.
    """

    def __init__(self, message: Any, data: Any = None, http_status_code: int = 200) -> None:
        super().__init__(message)
        self.msg = message
        self.data = data
        self.http_status_code = http_status_code


class FailedExecutionException(Exception):
    """To be only used to communicate failure codes/msgs
    by models to runner methods.
    """

    def __init__(
        self,
        message: Any,
        http_status_code: int = 500,
        clb_dict: Optional[types.Callback] = None,
    ) -> None:
        super().__init__(message)
        self.msg = message
        self.http_status_code = http_status_code
        self.clb_dict = clb_dict


class OutputOverwriteException(Exception):
    """To be raised when a model is trying to overwrite an output

    Args:
        Exception (_type_): _description_
    """

    def __init__(self, msg: str) -> None:
        super().__init__(msg)
