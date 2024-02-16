import json
from pathlib import Path
from typing import Any, Dict, List, Union

from clay import ModelWrapper

NOOP_CONFIG = str((Path(__file__).parent / "noop.yaml").absolute())


class NOOP(ModelWrapper):
    def setup(self):
        self.logger.info("Setup complete")

    async def preprocess(self, x: float) -> float:
        self.logger.info("Input recieved")
        return x

    async def inference(self, x: float) -> float:
        self.logger.info("Running inference")
        return x

    async def postprocess(self, x: float) -> float:
        self.logger.info("Returning results")
        return x


def make_noop_input(x: float = 5.0) -> str:
    inputs: List[Dict[str, Union[str, float]]] = [
        {"name": "x", "type": "float", "format": "number", "value": x},
    ]
    request: List[Dict[Any, Any]] = [{"name": "task_id", "type": "str", "format": "string", "value": "123456"}]
    request.extend(inputs)
    return json.dumps(request)
