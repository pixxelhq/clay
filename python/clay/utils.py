import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import yaml
from urllib3.util import parse_url


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


def get_io_dirmap(io: List[Any], workingDir: str) -> Dict[str, str]:
    paths = {}
    for i in io:
        expected_path = os.path.join(workingDir, i["name"])
        if os.path.exists(expected_path):
            paths[i["name"]] = expected_path
    return paths


def get_filename_from_remote(url: str) -> str:
    fragments = parse_url(url)
    if fragments.path is None:
        return ""
    return os.path.basename(fragments.path)


def pop_dict_with_err(d: Dict[Any, Any], key: Any) -> Tuple[Any, Optional[KeyError]]:
    val = None
    try:
        val = d.pop(key)
    except KeyError as exc:
        return val, exc
    return val, None


def convert_list_to_dict(l: List[Dict[str, Any]], primary_key: str) -> Dict[str, Any]:  # noqa: E741
    d = {}
    for li in l:
        d[li[primary_key]] = li
    return d


def get_current_utc_time_iso() -> str:
    return str(datetime.now(timezone.utc).isoformat())
