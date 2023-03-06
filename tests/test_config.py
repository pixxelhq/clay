import os
from typing import Union

import pytest
import yaml

from ramen import ModelWrapper
from ramen.config import get_config
from tests.testrepo.test_b import bfunc


@pytest.mark.asyncio
async def test_input_config_with_multi_types() -> None:
    test_dict = {
        "deployment": {
            "storage": [{"provider": "azure", "type": "str", "value": "some-container"}]
        },
        "model": {
            "init": [{"name": "a", "type": "str", "value": "hello world!"}],
            "inputs": [{"name": "i", "type": "int,array"}],
        },
    }
    with open("./tests/testrepo/test.yaml", "w") as f:
        yaml.dump(test_dict, f, default_flow_style=False)

    test_config = get_config("./tests/testrepo/test.yaml")
    assert (
        test_config.model.inputs["i"]["type"] == test_dict["model"]["inputs"][0]["type"]
    )

    class M(ModelWrapper):
        def setup(self, a: str) -> None:
            print("In setup: ", a)

        async def preprocess(self, i: Union[list, str]):
            return i

        async def inference(self, i: Union[list, str]):
            return i

        async def postprocess(self, res):
            return res

    toy_model = M("./tests/testrepo/test.yaml")
    toy_output = await toy_model.infer({"i": 1})
    assert toy_output["result"] == 1

    toy_output = await toy_model.infer({"i": [1, 2, 3]})
    assert toy_output["result"] == [1, 2, 3]

    os.remove("./tests/testrepo/test.yaml")


@pytest.mark.asyncio
async def test_input_config_multi_type_invalid_type() -> None:
    test_dict = {
        "deployment": {
            "storage": [{"provider": "azure", "type": "str", "value": "some-container"}]
        },
        "model": {
            "init": [{"name": "a", "type": "str", "value": "hello world!"}],
            "inputs": [{"name": "i", "type": "str,int"}],
        },
    }
    with open("./tests/testrepo/test-2.yaml", "w") as f:
        yaml.dump(test_dict, f, default_flow_style=False)

    test_config = get_config("./tests/testrepo/test-2.yaml")
    print(test_config.model.inputs)
    assert (
        test_config.model.inputs["i"]["type"] == test_dict["model"]["inputs"][0]["type"]
    )

    class M(ModelWrapper):
        def setup(self, a: str) -> None:
            print("In setup: ", a)

        async def preprocess(self, i: str):
            return bfunc() + i

        async def inference(self, i: str):
            return i

        async def postprocess(self, res):
            return res

    toy_model = M("./tests/testrepo/test-2.yaml")
    with pytest.raises(ValueError):
        await toy_model.infer({"i": [1, 2, 3]})

    os.remove("./tests/testrepo/test-2.yaml")
