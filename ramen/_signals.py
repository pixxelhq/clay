from typing import Any

from ramen.exceptions import FailedExecutionException, SuccessfulExecutionException


def success(message: Any = None) -> None:
    """calling ramen.success() returns execution from
    model to runner context. This behaviour might change
    in the future.
    """
    if message is None:
        message = "Success."
    raise SuccessfulExecutionException(message=message)


def failure(message: Any = None) -> None:
    """calling ramen.failure() returns execution from
    model to runner context. This behaviour might
    change in the future.
    """
    if message is None:
        message = "Failure."
    raise FailedExecutionException(message=message)
