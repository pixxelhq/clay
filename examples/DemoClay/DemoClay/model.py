from typing import Any, Dict

from clay.core import ModelWrapper
from clay.types import Data, Date, Number, Raster, String, Tabular, Vector


class DemoClay(ModelWrapper):
    def setup(self, weights, **hyperparameters) -> None:
        # download weights, initialize model,
        # setup directories, etc.
        pass

    async def preprocess(
        self,
        input1: Raster,
        input2: Vector,
        input3: Date,
        input4: String,
        input5: Number,
        input6: Tabular,
        extra: Data,
    ) -> Dict[str, Any]:
        # function takes inputs for a model
        # input name in the fucntion needs to match input name from spec file
        model_inputs, extra = None, None
        return {"model_inputs": model_inputs, "extra": extra}

    async def inference(self, model_inputs, extra) -> Dict[str, Any]:
        # simply run inference and return the results
        # and anything extra if required
        inference_results, extra = None, None
        return {"inference_results": inference_results, "extra": extra}

    async def postprocess(self, inference_results, extra) -> Dict[str, Data]:
        # perform any post-processing
        output_path1, output_path2 = "", ""
        return {
            "output1": Raster(name="output1", value=output_path1),
            "output2": Vector(name="output2", value=output_path2),
        }
