from typing import Any, Dict

# import geo
# import geojson

from clay import types as T
from clay.core import ModelWrapper


class DemoTest(ModelWrapper):
    def setup(self, seed: int) -> None:  # type: ignore
        # download weights, initialize model,
        # setup directories, etc.
        self.seed = seed

    async def preprocess(  # type: ignore
        self, some_raster: T.Raster, some_vector: T.Vector, some_string: T.String
    ) -> Dict[str, Any]:
        # `preprocess` takes inputs for a model
        # input name in the fucntion needs to match input name from the spec file
        self.logger.info(f"In pre-process. I can access all `self` parameters throughout the model: {self.seed}")
        return {"r": some_raster, "s": some_string, "v": some_vector}

    # type: ignore
    async def inference(self, r: T.Raster, s: T.String, v: T.Vector) -> Dict[str, Any]:
        # `inference` as the name suggests is the point wherein the model executes its core logic.
        # Feel free to write logic in this method or call another method from here. Anything works.
        # val = geo.mosaic(r)

        # self.logger.info(f"value returned from `geo.mosaic`: {val}")

        # with open(str(v.Value), "r") as f:
        #     v = geojson.load(f)
        return {"s": s, "v": v}

    async def postprocess(self, s: T.String, v: Any) -> Dict[str, T.Data]:  # type: ignore
        # perform any post-processing

        # mutating the string
        val = str(s.Value)
        new_string = "new string: " + val

        # self.logger.info(f"old vector: {v}")
        # with open("my-vector.geojson", "w+") as f:
        #     geojson.dump(v, f)
        return {
            "another_string": T.String(name="another_string", value=new_string),
            "vector": T.Vector(name="vector", value=v.Value),
        }
