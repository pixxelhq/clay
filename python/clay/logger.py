from __future__ import annotations

import io
import logging
import logging.config
import logging.handlers
import sys
from logging import Logger
from typing import Callable, Optional, Union

_DEFAULT_HANDLER_NAME = "clay_handler"
buffer_handler_name = "buffer_handler"
_default_formatter = logging.Formatter(
    "%(levelname)s - %(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s"  # noqa: E501
)


def add_function_to(cls: type, name: Union[str, None] = None) -> Callable:
    def set_cls_attr(func: Callable) -> None:
        nonlocal name
        if name is None:
            name = func.__name__
        setattr(cls, name, func)

    return set_cls_attr


def set_propogate(logger: Logger, propagate: bool) -> None:
    """
    Disables propogating logs to the root handler and only
    logs using the explicit handlers.
    """
    logger.propagate = propagate


def add_console_handler(logger: Logger, level: Union[int, None] = None) -> Logger:
    """
    Method to add the `default_handler` to the logger. `default_handler` logs msgs
    to the standard `sys.stdout` which is then printed onto the console. Use this
    handler if you wish for your logs to be printed into `sys.stdout` from where
    the logs would be  displayed onto the console or captured by other file
    watchers.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.set_name(_DEFAULT_HANDLER_NAME)
    handler.setFormatter(_default_formatter)
    if level is None:
        level = logger.level
    handler.setLevel(level=level)
    logger.addHandler(handler)
    return logger


def add_buffer_handler(logger: Logger, level: Union[int, None] = None) -> Logger:
    """
    Method to add the `buffer_handler` to the logger. `buffer_handler` logs msgs to
    an in-memory string buffer. The contents of this buffer can be retrieved by
    calling on `get_streamvalues()`.
    """
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.set_name(buffer_handler_name)
    handler.setFormatter(_default_formatter)
    if level is None:
        level = logger.level
    handler.setLevel(level)
    logger.addHandler(handler)
    return logger


def get_streamvalues(logger: Logger) -> Optional[str]:
    for handler in logger.handlers:
        if (
            isinstance(handler, logging.StreamHandler)
            and handler.name == buffer_handler_name
        ):
            assert isinstance(handler.stream, io.StringIO)
            pos = handler.stream.tell()
            handler.stream.seek(0)
            logs = handler.stream.getvalue()
            # putting the cursor back to where it was
            handler.stream.seek(pos)
            return logs


def ClayLogger(
    logger_name: str,
    propagate: bool = True,
    level: int = logging.INFO,
    create_console_handler: bool = False,
    create_buffer_handler: bool = False,
) -> Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = propagate
    if create_console_handler:
        add_console_handler(logger)
    if create_buffer_handler:
        add_buffer_handler(logger)
    return logger


add_function_to(Logger)(set_propogate)
add_function_to(Logger)(add_console_handler)
add_function_to(Logger)(add_buffer_handler)
add_function_to(Logger)(get_streamvalues)
