from typing import Any, Dict

from clay.core import BlockWrapper
import datatypes
import rasterio
import numpy

class {{.BlockName}}(BlockWrapper):
    def setup(self, weight: int, **hyperparameters) -> None:  # type: ignore
        # download weights, initialize block,
        # input name in the function needs to match the parameter name in the spec file
        # setup directories, etc.
        self.weight = weight

    async def preprocess(  # type: ignore
        self,
        input1: datatypes.String,
        input2: datatypes.Number,
    ) -> Dict[str, Any]:
        # function takes inputs for a block
        # input name in the function needs to match input name from spec file
        self.logger.warning(
            "In pre-process. Use self.logger for all logging. Avoid print statements"
        )
        self.logger.info(f"Input1 is {input1.value}")
        return {"input1": input1, "input2": input2}

    async def inference(self, input1: String, input2: Number) -> Dict[str, Any]:  # type: ignore
        # simply run inference and return the results
        # and anything extra if required
        self.logger.info("In inference. I can access all `self` parameters throughout the block ")
        return {"input1": input1, "input2": input2}

    async def postprocess(self, input1: String, input2: Number) -> Dict[str, Data]:  # type: ignore
        # perform any post-processing
        self.logger.info("In postprocessing")
        return {
            "output1": datatypes.Number(name="output1", value=input2.value),
        }
