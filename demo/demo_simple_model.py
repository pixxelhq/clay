# type: ignore

import sys
import time
from typing import Any

from ramen.core import ModelWrapper
from ramen.runners import JobRunner


class DemoSimpleModel(ModelWrapper):
    def setup(self, arg1: int, arg2: str) -> None:
        self.arg1 = arg1
        self.arg2 = arg2
        time.sleep(1)

    async def preprocess(self, input1: str) -> Any:
        time.sleep(1)
        return input1 + "B"

    async def inference(self, arg: str) -> Any:
        time.sleep(3)
        return arg + "C"

    async def postprocess(self, arg: str) -> Any:
        return arg


if __name__ == "__main__":
    args = sys.argv[1]

    jr = JobRunner(
        "demo",
        DemoSimpleModel,
        {"config": "demo_simple_model_config.yaml"},
    )

    jr.start([args])
