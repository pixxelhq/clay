import os
from typing import Any, Optional

import yaml


class Converters:
    @staticmethod
    def type_int(value: str) -> int:
        return int(value)

    @staticmethod
    def type_float(value: str) -> float:
        return float(value)

    @staticmethod
    def type_array(value: list) -> list:
        """just for consistency"""
        return value

    @staticmethod
    def type_str(value: str) -> str:
        """just for consistency"""
        if not isinstance(value, str):
            return str(value)
        return value

    @staticmethod
    def type_envvar(value: str) -> Optional[str]:
        return os.getenv(value)


def read_yaml(fp: str) -> dict:
    if not os.path.exists(fp):
        raise FileNotFoundError(f"{fp} not found")
    if not os.path.isfile(fp):
        raise IsADirectoryError(f"{fp} is a directory and not a file.")
    with open(fp, "r") as f:
        config = yaml.safe_load(f)
    return config


def get_value(d: dict) -> dict:
    tmp = {}
    tmp[d["name"]] = getattr(Converters, f"type_{d['type']}")(d["value"])
    return tmp


def to_tuple_if_required(x: Any) -> Any:
    if x is None:
        return x
    if not isinstance(x, tuple):
        return (x,)
    return x
