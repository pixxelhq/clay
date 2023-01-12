import copy
import logging
import logging.config
from typing import Any, Dict, Union

# TODO: remove `uvicorn.logging.DefaultFormatter` and bring it inside ramen


class _DefaultRamenLogConfig:

    _DEFAULT_FORMATTER = {
        "placeholder": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelname)s -%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s",  # noqa: E501
        }
    }
    _DEFAULT_HANDLER = {
        "placeholder": {
            "formatter": "",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        }
    }
    _DEFAULT_LOGGER = {
        "placeholder": {
            "handlers": [""],
            "level": "INFO",
            "propogate": "True",
        }
    }

    @classmethod
    def log_config_builder(cls, logger_name: str) -> Dict[str, Any]:

        _DEFAULT_FORMATTER = copy.deepcopy(cls._DEFAULT_FORMATTER)
        _DEFAULT_HANDLER = copy.deepcopy(cls._DEFAULT_HANDLER)
        _DEFAULT_LOGGER = copy.deepcopy(cls._DEFAULT_LOGGER)

        # creating the formatter
        _DEFAULT_FORMATTER[logger_name] = _DEFAULT_FORMATTER["placeholder"]
        del _DEFAULT_FORMATTER["placeholder"]

        # creating the handler
        _DEFAULT_HANDLER["placeholder"]["formatter"] = logger_name
        _DEFAULT_HANDLER[logger_name] = _DEFAULT_HANDLER["placeholder"]
        del _DEFAULT_HANDLER["placeholder"]

        # creating the logger
        _DEFAULT_LOGGER[logger_name] = _DEFAULT_LOGGER["placeholder"]
        _DEFAULT_LOGGER[logger_name]["handlers"] = [logger_name]
        del _DEFAULT_LOGGER["placeholder"]

        config = {
            "version": 1,
            "formatters": {logger_name: _DEFAULT_FORMATTER[logger_name]},
            "handlers": {logger_name: _DEFAULT_HANDLER[logger_name]},
            "loggers": {logger_name: _DEFAULT_LOGGER[logger_name]},
        }

        return config


def get_logger(
    identifier: str, log_config: Union[None, Dict[str, Any]] = None
) -> logging.Logger:
    if log_config is None:
        if identifier is None:
            raise ValueError("`identifier` cannot be None. Needs to be `str`")
        log_config = _DefaultRamenLogConfig.log_config_builder(identifier)
    logging.config.dictConfig(log_config)
    return logging.getLogger(identifier)
