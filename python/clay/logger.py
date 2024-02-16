from __future__ import annotations

import io
import logging
import logging.config
import logging.handlers
import sys
from logging import Logger
from typing import Callable, Optional, Union

_DEFAULT_HANDLER_NAME = "clay_handler"
_default_buffer_handler_name = "buffer_handler"
_default_console_handler_name = "console_handler"
_default_user_logs_handler_name = "user_logs_handler"
_default_formatter = logging.Formatter(
    "%(levelname)s - %(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s"  # noqa: E501
)
_user_logs_formatter = logging.Formatter("%(levelname)s - %(asctime)s - %(message)s")


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


def add_console_handler(
    logger: Logger,
    level: Union[int, None] = None,
    formatter: logging.Formatter = _default_formatter,
    handler_name: str = _default_console_handler_name,
) -> Logger:
    """
    Method to add the `default_handler` to the logger. `default_handler` logs msgs
    to the standard `sys.stdout` which is then printed onto the console. Use this
    handler if you wish for your logs to be printed into `sys.stdout` from where
    the logs would be  displayed onto the console or captured by other file
    watchers.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.set_name(handler_name)
    handler.setFormatter(formatter)
    if level is None:
        level = logger.level
    handler.setLevel(level=level)
    logger.addHandler(handler)
    return logger


def add_buffer_handler(
    logger: Logger,
    level: Union[int, None] = None,
    formatter: logging.Formatter = _default_formatter,
    handler_name: str = _default_buffer_handler_name,
) -> Logger:
    """
    Method to add the `buffer_handler` to the logger. `buffer_handler` logs msgs to
    an in-memory string buffer. The contents of this buffer can be retrieved by
    calling on `get_streamvalues()`.
    """
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.set_name(handler_name)
    handler.setFormatter(formatter)
    if level is None:
        level = logger.level
    handler.setLevel(level)
    logger.addHandler(handler)
    return logger


def add_user_logs_handler(
    logger: Logger,
    level: int = logging.INFO,
    formatter: logging.Formatter = _user_logs_formatter,
    handler_name: str = _default_user_logs_handler_name,
) -> Logger:
    """
    Method to add the `buffer_handler` to the logger. `buffer_handler` logs msgs to
    an in-memory string buffer. The contents of this buffer can be retrieved by
    calling on `get_streamvalues()`.
    """
    add_buffer_handler(logger=logger, level=level, formatter=formatter, handler_name=handler_name)
    return logger


def get_streamvalues(logger: Logger, handler_name: str = _default_buffer_handler_name) -> Optional[str]:
    """Reads logs from the stream in the `handler_name` handler while retaining
    the cursor position

    :param logger: logger to read logs from
    :param handler_name: name of the handler, defaults to _default_buffer_handler_name
    :return: logs
    """
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.name == handler_name:
            pos = handler.stream.tell()
            handler.stream.seek(0)
            logs = handler.stream.getvalue()
            # putting the cursor back to where it was
            handler.stream.seek(pos)
            return logs


def get_buffer_logs(logger: Logger, handler_name: str = _default_buffer_handler_name) -> Optional[str]:
    """Reads logs stored in a string buffer in a handler named `handler_name`
    intended specifically for all the user logs

    :param logger: logger to read logs from
    :param handler_name: name of the handler containing the buffer,
        defaults to _default_buffer_handler_name
    :return: logs
    """
    return get_streamvalues(logger, handler_name=handler_name)


def get_user_logs(logger: Logger, handler_name: str = _default_user_logs_handler_name) -> Optional[str]:
    """Reads logs stored in a string buffer in a handler named `handler_name`
    intended specifically only for user viewable logs written at INFO level

    :param logger: logger to read logs from
    :param handler_name: name of the handler containing the buffer,
        defaults to _default_user_logs_handler_name
    :return: logs
    """
    return get_streamvalues(logger, handler_name=handler_name)


def ClayLogger(
    logger_name: str,
    propagate: bool = True,
    level: int = logging.DEBUG,
    create_console_handler: bool = False,
    create_buffer_handler: bool = False,
    create_user_logs_handler: bool = False,
) -> Logger:
    """Creates a Python logger with custom tooling to tightly integrate it with Orchestrator
    and the rest of Pixxel's Platform. The created logger will log to multiple streams in
    different ways to serve varying levels of information to both internal and external
    stakeholders

    :param logger_name: name of the logger
    :param propagate: whether to propagate the logger's settings to children loggers,
        defaults to True
    :param level: logging level, defaults to logging.DEBUG
    :param create_console_handler: Enable logging to console / terminal, defaults to False
    :param create_buffer_handler: Enable storing logs in a string buffer,
        defaults to False
    :param create_user_logs_handler: Enable storing user viewable logs (INFO LEVEL) in a
        separate stream, defaults to False
    :return: Python logger supercharged with Clay / Orchestrator integrations
    """
    if logger_name in logging.Logger.manager.loggerDict.keys():
        logger = logging.getLogger(logger_name)
        logger.warning("Using existing logger without re-initialising.")
        return logger

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = propagate
    if create_console_handler:
        add_console_handler(logger)
    if create_buffer_handler:
        add_buffer_handler(logger)
    if create_user_logs_handler:
        add_user_logs_handler(logger, level=logging.INFO)
    return logger


add_function_to(Logger)(set_propogate)
add_function_to(Logger)(add_console_handler)
add_function_to(Logger)(add_buffer_handler)
add_function_to(Logger)(add_user_logs_handler)
add_function_to(Logger)(get_streamvalues)
add_function_to(Logger)(get_buffer_logs)
add_function_to(Logger)(get_user_logs)
