import clay
from clay import ModelWrapper
from clay.runners import HTTPRunner
from test_b import bfunc


class M(ModelWrapper):
    def setup(self, a: str, x: list) -> None:
        print("In setup: ", a)

    async def preprocess(self, i: str):
        return bfunc() + i

    async def inference(self, i: str):
        if i == "baa":
            return clay.failure("failing")
        return i

    async def postprocess(self, res):
        return res


if __name__ == "__main__":
    m = HTTPRunner("demo", M, {"config": "/home/espoir/clay/tests/testrepo/config.yaml"})
    m.start()
