# type: ignore
"""Integration test: BlockWrapper.infer() must surface typed `.value`
to user code, restoring the Python type declared in clay.yaml.

The casting itself lives in pixxel-datatypes (see test_data.py); this test only
verifies the wiring between clay-framework and the new typed view.
"""

import asyncio
from pathlib import Path
from typing import Any

import pytest
import yaml

import datatypes
from clay import BlockWrapper


@pytest.fixture
def typed_config(tmp_path: Path) -> str:
    spec = {
        "kind": "block",
        "type": "processing",
        "name": "TypedBlock",
        "description": "Fixture",
        "parameters": [],
        "inputs": [
            {"name": "num", "format": "number", "type": "int"},
            {"name": "ratio", "format": "number", "type": "float"},
            {"name": "flag", "format": "string", "type": "bool"},
            {"name": "label", "format": "string", "type": "str"},
        ],
        "outputs": [
            {"name": "output1", "format": "number", "type": "int"},
        ],
    }
    cfg = tmp_path / "typed.yaml"
    cfg.write_text(yaml.safe_dump(spec))
    return str(cfg)


def _wrap(name: str, fmt: str, declared_type: str, value: Any) -> datatypes.DataWrapper:
    return datatypes.FromDict(
        {"name": name, "format": fmt, "type": declared_type, "value": value},
        wrap=True,
    )


def test_infer_surfaces_typed_values_from_proto(typed_config: str) -> None:
    """Regression: input.value * int should multiply numerically, not repeat strings."""

    class WeightedBlock(BlockWrapper):
        def setup(self) -> None:
            self.weight = 5
            self.result: int = 0
            self.captured: dict = {}

        async def preprocess(self, **inputs: Any) -> dict:
            return inputs

        async def inference(self, num: Any, ratio: Any, flag: Any, label: Any) -> dict:
            self.captured = {
                "num": num.value,
                "ratio": ratio.value,
                "flag": flag.value,
                "label": label.value,
            }
            self.result = num.value * self.weight
            return {"output1": num}

        async def postprocess(self, output1: Any) -> dict:
            return {"output1": datatypes.Number(name="output1", value=str(self.result))}

    block = WeightedBlock(config=typed_config)
    inputs = {
        "num": _wrap("num", "number", "int", 5),
        "ratio": _wrap("ratio", "number", "float", 1.5),
        "flag": _wrap("flag", "string", "bool", True),
        "label": _wrap("label", "string", "str", "hello"),
    }
    asyncio.get_event_loop().run_until_complete(block.infer(inputs=inputs))

    assert block.result == 25
    assert block.captured == {"num": 5, "ratio": 1.5, "flag": True, "label": "hello"}
    assert isinstance(block.captured["num"], int)
    assert isinstance(block.captured["ratio"], float)
    assert block.captured["flag"] is True
