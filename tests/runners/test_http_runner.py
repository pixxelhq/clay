import unittest
from typing import Any, Dict

from fastapi.testclient import TestClient

import ramen
from ramen import ModelWrapper
from ramen.runners import HTTPRunner


class M(ModelWrapper):
    def setup(self, a: str, x: list):
        pass

    async def preprocess(self, i: str) -> Any:
        if i == "f":
            ramen.failure("Failed", 500)
        return 1, 2, {"a": 123}

    async def inference(self, a: int, b: int, c: Dict[str, int]) -> Any:
        return "c"

    async def postprocess(self, x: str) -> Any:
        return "x"


class TestHTTPRunner(unittest.TestCase):
    def setUp(self) -> None:
        self._modelcls = M
        self._modelargs = {"config": "tests/testrepo/config.yaml"}

    def test_jobrunner_init(self) -> None:
        HTTPRunner(
            "demomodel",
            self._modelcls,
            self._modelargs,
        )

    def test_root(self):
        m = HTTPRunner(
            "demomodel",
            self._modelcls,
            self._modelargs,
        )
        m._init_fastapi_app()
        app = m._app
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == "This is root!"

    def test_sucess(self):
        m = HTTPRunner("demomodel", self._modelcls, self._modelargs)
        m._init_model()
        m._init_model_inference_event_loop()
        m._init_fastapi_app()
        app = m._app
        client = TestClient(app)
        response = client.post("/infer", data='{"i": "a"}')
        assert response.status_code == 200
        assert response.content == b"x"

    def test_failure(self):
        m = HTTPRunner("demomodel", self._modelcls, self._modelargs)
        m._init_model()
        m._init_model_inference_event_loop()
        m._init_fastapi_app()
        app = m._app
        client = TestClient(app)
        response = client.post("/infer", data='{"i": "f"}')
        assert response.status_code == 500
        assert response.content == b"status code: 500 message:Failed"
