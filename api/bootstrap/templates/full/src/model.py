from typing import Any, Dict

from clay.core import ModelWrapper
from clay.types import Date, Number, Raster, String, Tabular, Vector, Data


class {{.ModelName}}(ModelWrapper):
    def setup(self, weights: int, **hyperparameters) -> None:   # type: ignore
        # download weights, initialize model,
        # setup directories, etc.
        self.weights = weights

    async def preprocess(    # type: ignore
        self,
        input1: Raster,
        input2: Vector,
        input3: Date,
        input4: String,
        input5: Number,
        input6: Tabular,
        extra: Data
    ) -> Dict[str, Any]:   # type: ignore
        # function takes inputs for a model
        # input name in the function needs to match input name from spec file
        self.logger.warning("In pre-process. Use self.logger for all logging. Avoid print statements")
        return {"input1": input1, "extra": extra}

    async def inference(self, input1: Raster, extra: Data) -> Dict[str, Any]:   # type: ignore
        # simply run inference and return the results
        # and anything extra if required
        self.logger.info("In inference. I can access all `self` parameters throughout the model ")
        inference_results = input1.Value
        return {"inference_results": inference_results, "extra": extra}

    async def postprocess(self, inference_results, extra) -> Dict[str, Data]:   # type: ignore
        # perform any post-processing
        self.logger.info("In postprocessing")
        output_path1, output_path2 = 'output_raster.tif', 'output_vector.geojson'
        return {
            "output1": Raster(name="output1", value=output_path1),
            "output2": Vector(name="output2", value=output_path2),
        }
