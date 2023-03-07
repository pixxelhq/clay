from ramen.models import AppConfig
from ramen.utils import read_yaml


def test_deployment_config_parsing() -> None:
    config = AppConfig.parse(read_yaml("tests/testrepo/config.yaml"))
    assert isinstance(config, AppConfig)
