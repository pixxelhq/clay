from clay import ModelWrapper, create_server
from test_b import bfunc


class M(ModelWrapper):
    def setup(self) -> None:
        print("In setup")

    async def preprocess(self, i: str):
        return bfunc() + i

    async def inference(self, i: str):
        self.logger.info("Something")
        return i

    async def postprocess(self, res: str):
        return res


if __name__ == "__main__":
    m = create_server(M, "./config.yaml")
    m.start()
