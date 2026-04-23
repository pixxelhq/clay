from pathlib import Path
from typing import Any, Tuple

from clay import BlockWrapper

DUMMY_BLOCK_CONFIG = str((Path(__file__).parent / "dummy_block.yaml").absolute())


class DummyBlock(BlockWrapper):
    def setup(self, slope: float, intercept: float) -> None:
        self.slope = slope
        self.intercept = intercept
        self.logger.info("Setup complete")

    async def preprocess(self, x: float, info: str) -> Tuple[float, str]:
        self.set_progress(7)
        return x, info

    async def inference(self, x: float, info: str) -> Tuple[float, str]:
        y = self.slope * x + self.intercept
        equation = f"{y} = {self.slope} * {x} + {self.intercept}\n{info}"
        return y, equation

    async def postprocess(self, y: float, equation: str) -> Any:
        return y, equation
