from typing import Any

from .exceptions import FailedExecutionException, SuccessfulExecutionException


def success(message: Any = None, http_status_code: int = 200) -> None:
    """calling ramen.success() returns execution from
    model to runner context. This behaviour might change
    in the future.
    """
    if message is None:
        message = "Success."
    raise SuccessfulExecutionException(message=message, http_status_code=http_status_code)


def failure(message: Any = None, logs: Any = "", http_status_code: int = 500) -> None:
    """calling ramen.failure() returns execution from
    model to runner context. This behaviour might
    change in the future.
    """
    if message is None:
        message = "Failure."
    raise FailedExecutionException(
        message=message, logs=logs, http_status_code=http_status_code
    )
