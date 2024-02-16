from typing import Any, Optional

from clay import types
from clay.exceptions import FailedExecutionException, SuccessfulExecutionException


def success(message: Any = None, http_status_code: int = 200) -> None:
    """calling clay.success() returns execution from
    model to runner context. This behaviour might change
    in the future.
    """
    if message is None:
        message = "Success."
    raise SuccessfulExecutionException(message=message, http_status_code=http_status_code)


def failure(
    message: Any = None,
    http_status_code: int = 500,
    clb_dict: Optional[types.Callback] = None,
) -> None:
    """calling clay.failure() returns execution from
    model to runner context. This behaviour might
    change in the future.
    """
    if message is None:
        message = "Failure."
    raise FailedExecutionException(message=message, clb_dict=clb_dict, http_status_code=http_status_code)
