from typing import Any, Dict, TypeVar, Union

import pydantic

from ramen.utils import Converters, get_value

T = TypeVar("T")


class StorageConfig(pydantic.BaseModel):
    provider: str
    value: str


class DeploymentConfig:
    storage: Union[StorageConfig, None] = None

    @classmethod
    def parse(cls, config: dict) -> Any:
        assert "storage" in config  # currently only supporting storage
        assert len(config) == 1  # currently only one storage option supported
        d = {}
        for item in config["storage"]:
            d["provider"] = item["provider"]
            d["value"] = getattr(Converters, f"type_{item['type']}")(item["value"])

        dc = DeploymentConfig()
        dc.__setattr__("storage", StorageConfig.parse_obj(d))
        return dc


class ModelConfig:
    init: Dict[str, Any] = {}
    inputs: Dict[str, Any] = {}

    @classmethod
    def parse(cls, config: dict) -> Any:
        mc = ModelConfig()
        if "init" in config:
            for item in config["init"]:
                processed_item = get_value(item)
                mc.init.update(processed_item)
        for item in config["inputs"]:
            mc.inputs[item["name"]] = {"type": item["type"]}
        return mc


class AppConfig:
    deployment: DeploymentConfig
    model: ModelConfig

    @classmethod
    def parse(cls, config: dict) -> Any:
        ac = AppConfig()  # FIND A NEATER WAY FOR THIS
        # parsing `deployment` settings
        if "deployment" in config:
            deployment = DeploymentConfig.parse(config["deployment"])
            ac.__setattr__("deployment", deployment)
        model = ModelConfig.parse(config["model"])
        ac.__setattr__("model", model)

        return ac
