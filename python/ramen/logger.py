from __future__ import annotations

import io
import logging
import logging.config
import logging.handlers
import sys
import warnings
from typing import Any, TypeVar, Union

T = TypeVar("T", bound="RamenLogger")


class RamenLogger(object):

    _DEFAULT_HANDLER_NAME: str = "ramen_handler"

    def __init__(
        self, logger_name: str, propogate: bool, level: int = logging.INFO
    ) -> None:

        self._logger = logging.getLogger(logger_name)
        self._default_formatter = logging.Formatter(
            "%(levelname)s - %(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s"  # noqa: E501
        )
        self.level = level
        self.set_propogate(propogate)
        if level is not None:
            self._logger.setLevel(level)

    def set_propogate(self, val: bool = False) -> None:
        # Disables propogating logs to the root handler and only
        # logs using the explicit handlers.
        self._logger.propagate = val

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def level(self) -> int:
        return self._level

    @level.setter
    def level(self, val: int) -> None:
        self._level = val

    def info(self, msg: Any, exc_info: int = 0) -> None:
        self.logger.info(msg=msg, exc_info=exc_info)  # type: ignore

    def debug(self, msg: Any, exc_info: int = 0) -> None:
        self.logger.debug(msg=msg, exc_info=exc_info)  # type: ignore

    def warning(self, msg: Any, exc_info: int = 1) -> None:
        self.logger.warn(msg, exc_info=exc_info)  # type: ignore

    def error(self, msg: Any, exc_info: int = 1) -> None:
        self.logger.error(msg, exc_info=exc_info)  # type: ignore

    def critical(self, msg: Any, exc_info: int = 1) -> None:
        self.logger.critical(msg=msg, exc_info=exc_info)  # type: ignore

    def add_console_handler(self, level: Union[int, None] = None) -> RamenLogger:
        # Method to add the `default_handler` to the logger. `default_handler` logs msgs
        # to the standard `sys.stdout` which is then printed onto the console. Use this
        # handler if you wish for your logs to be printed into `sys.stdout` from where
        # the logs would be  displayed onto the console or captured by other file
        # watchers.
        h = logging.StreamHandler(sys.stdout)
        h.set_name(self._DEFAULT_HANDLER_NAME)
        h.setFormatter(self._default_formatter)
        if level is None:
            level = self.level
        h.setLevel(level=level)
        self._logger.addHandler(h)
        return self

    def add_buffer_handler(self, level: Union[int, None] = None) -> RamenLogger:
        # Method to add the `buffer_handler` to the logger. `buffer_handler` logs msgs to
        # an in-memory string buffer. The contents of this buffer can be retrieved by
        # calling on `get_streamvalues()`.
        self.stream = io.StringIO()
        h = logging.StreamHandler(self.stream)
        h.set_name("buffer_handler")
        h.setFormatter(self._default_formatter)
        if level is None:
            level = self.level
        h.setLevel(level)
        self._logger.addHandler(h)
        return self

    @property
    def stream(self) -> Any:
        if not hasattr(self, "_stream"):
            raise ValueError(f"{self.__class__} has no property `stream`")
        return self._stream

    @stream.setter
    def stream(self, val: Any) -> None:
        self._stream = val

    def get_streamvalues(self) -> Any:
        if not hasattr(self, "_stream"):
            warnings.warn(f"{self.__class__} has no property `stream`", RuntimeWarning)
            return ""
        self.stream.seek(0)
        return self.stream.getvalue()
