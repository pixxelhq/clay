import os
from contextlib import contextmanager
from typing import Any


@contextmanager
def set_envvar(key: str, value: Any):
    old_value = None
    if key in os.environ:
        old_value = os.environ[key]
    os.environ[key] = value
    try:
        yield
    finally:
        if old_value is not None:
            os.environ[key] = old_value
        else:
            os.environ.pop(key)
