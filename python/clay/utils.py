import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

import yaml

def dict_to_namespace(d: dict) -> SimpleNamespace:
    """
    Convert a dictionary into a namespace object recursively.
    """
    namespace = SimpleNamespace(**d)
    for key, value in d.items():
        if isinstance(value, dict):
            setattr(namespace, key, dict_to_namespace(value))
    return namespace


def yaml_to_namespace(file_path: Union[Path, str]) -> SimpleNamespace:
    """
    Load a YAML file and convert it to a namespace object recursively.
    """
    with open(file_path, "r") as file:
        yaml_dict = yaml.safe_load(file)
    return dict_to_namespace(yaml_dict)


def noop(x: Any) -> Any:
    return x


PRIMITIVE_TYPES: Dict[str, Callable] = defaultdict(lambda: str)
PRIMITIVE_TYPES.update(
    {
        "string": str,
        "str": str,
        "path": Path,
        "url": str,
        "int": int,
        "Int": int,
        "float": float,
        "Float": float,
        "list": noop,
        "List": noop,
        "bool": bool,
        "boolean": bool,
        "dict": noop,
        "Dict": noop,
    }
)


def cast_inputs(value: Any, dtype: str) -> Any:
    return PRIMITIVE_TYPES[dtype.lower()](value)


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
        if not isinstance(value, list):
            raise TypeError(f"`{value}` is not a `list`")
        return value

    @staticmethod
    def type_str(value: str) -> str:
        """just for consistency"""
        if not isinstance(value, str):
            if isinstance(value, Iterable):
                raise TypeError(f"`value` of {type(value)} cannot be typecasted to string")
            return str(value)
        return value

    @staticmethod
    def type_envvar(value: str) -> Optional[str]:
        return os.getenv(value)

def get_value(d: dict) -> dict:
    tmp = {}
    tmp[d["name"]] = getattr(Converters, f"type_{d['type']}")(d["value"])
    return tmp


def convert_list_to_dict(l: List[Dict[str, Any]], primary_key: str) -> Dict[str, Any]:  # noqa: E741
    d = {}
    for li in l:
        d[li[primary_key]] = li
    return d


def get_current_utc_time_iso() -> str:
    return str(datetime.now(timezone.utc).isoformat())