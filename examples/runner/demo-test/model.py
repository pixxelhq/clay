from typing import Any, Dict

import geo
# import geojson
import datatypes as T
# from clay import types as T
from clay.core import ModelWrapper
from clay.core import set_disclaimer

class DemoTest(ModelWrapper):
    def setup(self, seed: int) -> None:  # type: ignore
        # download weights, initialize model,
        # setup directories, etc.
        self.seed = seed

    async def preprocess(  # type: ignore
        self, some_raster: T.Raster, some_vector: T.Vector
    ) -> Dict[str, Any]:
        # `preprocess` takes inputs for a model
        # input name in the fucntion needs to match input name from the spec file
        geo.add(1, 2)
        self.logger.info(f"In pre-process. I can access all `self` parameters throughout the model: {self.seed}")
        return {"r": some_raster,  "v": some_vector}

    # type: ignore
    async def inference(self, r: T.Raster,  v: T.Vector) -> Dict[str, Any]:
        # `inference` as the name suggests is the point wherein the model executes its core logic.
        # Feel free to write logic in this method or call another method from here. Anything works.
        # val = geo.mosaic(r)
        self.add_asset("raster.tif","some_raster" )
        # self.logger.info(f"value returned from `geo.mosaic`: {val}")
        set_disclaimer("This is a disclaimer")
        # with open(str(v.Value), "r") as f:
        #     v = geojson.load(f)
        return { "v": v}

    async def postprocess(self,  v: Any) -> Dict[str, T.Data]:  # type: ignore
        # perform any post-processing

        # mutating the string
        # val = str(s.value)
        # new_string = "new string: " + val

        # self.logger.info(f"old vector: {v}")
        # with open("my-vector.geojson", "w+") as f:
        #     geojson.dump(v, f)
        return {
            "vector": T.Vector(name="vector", value=v.value),
            "raster": T.Raster(name="raster", value=v.value),
            "raster2": T.Raster(name="raster2", value=v.value),
            "raster3": T.Raster(name="raster3", value=v.value),
        }
