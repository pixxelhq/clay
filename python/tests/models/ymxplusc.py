import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ramen import ModelWrapper

YMXPLUSC_CONFIG = str((Path(__file__).parent / "ymxplusc.yaml").absolute())


class YMXPLUSC(ModelWrapper):
    def setup(self, slope: float, intercept: float):
        self.slope = slope
        self.intercept = intercept
        self.logger.info("Setup complete")

    async def preprocess(self, x: float, info: str) -> Tuple[float, str]:
        self.logger.info("Input recieved")
        return x, info

    async def inference(self, x: float, info: str) -> Tuple[float, str]:
        y = self.slope * x + self.intercept
        equation = f"{y} = {self.slope} * {x} + {self.intercept}\n{info}"
        return y, equation

    async def postprocess(self, y: float, equation: str) -> Tuple[float, str]:
        self.logger.info(f"Computation complete: {equation}")
        return y, equation


def make_ymxplusc_input(x: float = 5.0, info: str = "Hopefully this works.") -> str:
    inputs: List[Dict[Any, Any]] = [
        {"name": "x", "type": "float", "format": "number", "value": x},
        {
            "name": "info",
            "type": "str",
            "format": "string",
            "value": info,
        },
    ]
    request: List[Dict[Any, Any]] = [
        {"name": "task_id", "type": "str", "format": "string", "value": "123456"}
    ]
    request.extend(inputs)
    return json.dumps(request)
