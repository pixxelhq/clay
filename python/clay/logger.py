import io
import json
import logging
import logging.config
import logging.handlers
import sys
import warnings
from datetime import datetime
from logging import Logger
from typing import Any, Callable, Optional, TypeVar, Union

_DEFAULT_HANDLER_NAME = "clay_handler"
_default_buffer_handler_name = "buffer_handler"
_default_console_handler_name = "console_handler"
T = TypeVar("T")


def stringify(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj)
    except TypeError:
        return str(obj)


def recursively_stringify_if_not_serializable(obj: T) -> Union[T, str]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = recursively_stringify_if_not_serializable(v)
    try:
        # we don't actually want to dump it. We just want to see if it's possible and then return the
        # dict as is if it is possible.
        json.dumps(obj)
    except TypeError:
        return str(obj)
    else:
        return obj


class JSONFormatter(logging.Formatter):
    """
    Python logging formatter that outputs everything as a JSON
    """

    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """
        Override formatTime to use UTC time for the timestamp.

        :param record: The log record containing the time
        :param datefmt: Date format string

        :return: Formatted UTC time
        """
        ct = datetime.utcfromtimestamp(record.created)
        if datefmt:
            return ct.strftime(datefmt)
        else:
            return ct.isoformat() + "Z"  # ISO 8601 format in UTC

    def generate_stack_trace_if_exc_info(self, record: logging.LogRecord) -> str:
        """
        Creates a printable stack trace from `record` if it has `exc_info`
        :param record: Log Record object
        :return: stack trace if possible, else empty string
        """
        stack_trace = f"\n{super().format(record)}\n" if record.exc_info else ""
        return stack_trace

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record=record, datefmt=self.datefmt)

        log_entry = {
            "level": record.levelname,
            "timestamp": timestamp,
            "logger": f"{record.name}",
            "loc": f"{record.filename}:{record.funcName}:{record.lineno}",
            "message": recursively_stringify_if_not_serializable(record.getMessage()),
        }

        # we use `stringify` instead of `json.dumps` so that in the rare case that a logged object
        # is not JSON serializable, we can still convert it to a string as a fallback option
        # and avoid the block failing because of a logging issue.
        return stringify(log_entry) + self.generate_stack_trace_if_exc_info(record)


_default_formatter = JSONFormatter()


def raise_param_deprecation_warning(param_name: str, msg: Union[str, None] = None) -> None:
    """Raises a depreciation warning when called.

    We set stack level to 2 to help the user of the function identify the location in their code where the
    deprecated function is called, not where the warning is issued within the function itself.
    :param
    :raises DeprecationWarning: Indicates the function is deprecated.
    """
    warnings.warn(
        msg
        or f"Using `{param_name}` when initialising the Claylogger is deprecated and has no effect. "
        "It will be removed in a future version.",
        category=DeprecationWarning,
        stacklevel=2,
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
    calling `get_streamvalues()` on the logger with `_default_buffer_handler_name`.
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


def get_streamvalues(logger: Logger, handler_name: str = _default_console_handler_name) -> Optional[str]:
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


def ClayLogger(
    logger_name: str,
    propagate: bool = True,
    level: int = logging.INFO,
    create_console_handler: Optional[bool] = None,
    create_buffer_handler: Optional[bool] = None,
    create_user_logs_handler: Optional[bool] = None,
) -> Logger:
    """Creates a Python logger with `logger_name` and `level` with JSON output.

    USAGE
    -----
    >>> import logging
    >>> from clay.logger import ClayLogger
    >>> logger = ClayLogger(logger_name='my-logger', level=logging.DEBUG)
    >>> logger.info("useful information")
    {"level": "INFO", "timestamp": "2024-03-21T05:28:27.435454Z", "logger": "my-logger", "loc": "file_name.py:function_name:124", "message": "useful information"}

    :param logger_name: name of the logger
    :param propagate: whether to propagate the logger's settings to children loggers,
        defaults to True
    :param level: logging level, defaults to logging.INFO
    :param create_console_handler: deprecated, has no effect
    :param create_buffer_handler: deprecated, has no effect
    :param create_user_logs_handler: deprecated, has no effect

    :return: Python logger configured with JSON formatting and other provided options
    """
    # raise deprecation warnings appropriately
    if create_console_handler:
        raise_param_deprecation_warning("create_console_handler")
    if create_buffer_handler:
        raise_param_deprecation_warning("create_buffer_handler")
    if create_user_logs_handler:
        raise_param_deprecation_warning("create_user_logs_handler")

    if logger_name in logging.Logger.manager.loggerDict.keys():
        logger = logging.getLogger(logger_name)
        logger.warning("Using existing logger without re-initialising.")
        return logger

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = propagate
    add_console_handler(logger, level=level)
    return logger


add_function_to(Logger)(set_propogate)
add_function_to(Logger)(add_console_handler)
add_function_to(Logger)(add_buffer_handler)
add_function_to(Logger)(get_streamvalues)
add_function_to(Logger)(get_buffer_logs)
