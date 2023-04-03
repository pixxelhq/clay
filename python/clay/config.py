from functools import lru_cache

from clay.models import AppConfig
from clay.utils import read_yaml

__SUPPORTED_CONFIG_OPTIONS__ = {"deployment": ["storage"], "model": ["init", "inputs"]}


@lru_cache(maxsize=3)
def get_config(fp: str) -> AppConfig:
    config_file = read_yaml(fp)
    return AppConfig.parse(config_file)
