from typing import Any

from clay.exceptions import FailedExecutionException


def failure(
    message: Any = None,
    http_status_code: int = 500,
) -> None:
    """calling clay.failure() returns execution from
    block to runner context. This behaviour might
    change in the future.
    """
    if message is None:
        message = "Failure."
    raise FailedExecutionException(
        message=message,
        http_status_code=http_status_code,
    )
