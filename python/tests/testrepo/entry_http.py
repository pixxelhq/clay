from test_b import bfunc

import ramen
from ramen import ModelWrapper
from ramen.runners import HTTPRunner


class M(ModelWrapper):
    def setup(self, a: str, x: list) -> None:
        print("In setup: ", a)

    async def preprocess(self, i: str):
        return bfunc() + i

    async def inference(self, i: str):
        if i == "baa":
            return ramen.failure("failing")
        return i

    async def postprocess(self, res):
        return res


if __name__ == "__main__":
    m = HTTPRunner("demo", M, {"config": "/home/espoir/ramen/tests/testrepo/config.yaml"})
    m.start()
