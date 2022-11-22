from test_b import bfunc

from ramen import ModelWrapper, create_server


class M(ModelWrapper):
    def setup(self, a: str, x: list) -> None:
        print("In setup: ", a)

    async def preprocess(self, i: str):
        return bfunc() + i

    async def inference(self, i: str):
        return i

    async def postprocess(self, res):
        return res


if __name__ == "__main__":
    m = create_server(M, "./config.yaml")
    m.start()
