"""
import unittest
from typing import Any, Dict
from unittest import mock

import pytest
from fastapi.testclient import TestClient

import clay
from clay import ModelWrapper
from clay.core import ModelStates
from clay.runners import HTTPRunner

from ..models.ymxplusc import YMXPLUSC, YMXPLUSC_CONFIG, make_ymxplusc_input

# pytest.skip("skipping http runner tests for now.", allow_module_level=True)


class M(ModelWrapper):
    def setup(self, a: str, x: list):
        pass

    async def preprocess(self, i: str) -> Any:
        if i == "f":
            clay.failure("Failed", 500)
        return 1, 2, {"a": 123}

    async def inference(self, a: int, b: int, c: Dict[str, int]) -> Any:
        return "c"

    async def postprocess(self, x: str) -> Any:
        return "x"


class TestHTTPRunner(unittest.TestCase):
    def setUp(self) -> None:
        self._modelcls = YMXPLUSC
        self._modelargs = {"config": YMXPLUSC_CONFIG}

    def test_jobrunner_init(self) -> None:
        HTTPRunner(
            YMXPLUSC.__name__,
            self._modelcls,
            self._modelargs,
        )

    def test_root(self):
        m = HTTPRunner(
            YMXPLUSC.__name__,
            self._modelcls,
            self._modelargs,
        )
        m._init_fastapi_app()
        app = m._app
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == "This is root!"

    def test_inference(self):
        m = HTTPRunner(
            YMXPLUSC.__name__,
            self._modelcls,
            self._modelargs,
        )
        m._init_model()
        m._init_model_inference_event_loop()
        m._init_fastapi_app()
        app = m._app
        client = TestClient(app)
        inp = make_ymxplusc_input()
        response = client.post("/infer", data=inp)
        assert response.status_code == 200

    @pytest.mark.skip(
        reason="no way of currently testing this until Orchestrator is up and running"
    )
    @mock.patch("clay.core.requests.post")
    def test_sucess(self, mock_post: Any):
        mock_response = mock.Mock()
        mock_response.json.return_value = {"successful_update": "True", "err": ""}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        m = HTTPRunner("demomodel", self._modelcls, self._modelargs)

        # Not using `m.start` since that is blocking.
        m._init_model()
        m._init_model_inference_event_loop()
        m._init_fastapi_app()
        app = m._app
        client = TestClient(app)
        response = client.post("/infer", data='{"i": "a"}')

        call_args = mock_post.call_args_list

        assert response.status_code == 200
        assert response.content == b"x"

        # Here we assert that there should have been two state updates,
        # 1. State change to `TaskInprogress`
        # 2. State change to `TaskCompleted`
        # To verify this, we intercept the POST calls being made to the
        # `ORCHESTRATOR_URL` and check the json being sent there.
        assert call_args[0].kwargs["json"]["state"] == ModelStates.INPROGRESS.value
        assert call_args[0].kwargs["json"]["result"] == {}
        assert call_args[0].kwargs["json"]["logs"] == ""

        assert call_args[1].kwargs["json"]["state"] == ModelStates.COMPLETED.value
        assert call_args[1].kwargs["json"]["result"] == "x"

    @pytest.mark.skip(
        reason="no way of currently testing this until Orchestrator is up and running"
    )
    @mock.patch("clay.core.requests.post")
    def test_failure(self, mock_post: Any):
        mock_response = mock.Mock()
        mock_response.json.return_value = {"successful_update": "True", "err": ""}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        m = HTTPRunner("demomodel", self._modelcls, self._modelargs)
        m._init_model()
        m._init_model_inference_event_loop()
        m._init_fastapi_app()
        app = m._app
        client = TestClient(app)
        response = client.post("/infer", data='{"i": "f"}')
        call_args = mock_post.call_args_list

        assert response.status_code == 500
        assert response.content == b"status code: 500 message:Failed"

        # Here we assert that there should have been two state updates,
        # 1. State change to `TaskInprogress`
        # 2. State change to `TaskCompleted`
        # To verify this, we intercept the POST calls being made to the
        # `ORCHESTRATOR_URL` and check the json being sent there.
        assert call_args[0].kwargs["json"]["state"] == ModelStates.INPROGRESS.value
        assert call_args[0].kwargs["json"]["result"] == {}
        assert call_args[0].kwargs["json"]["logs"] == ""

        assert call_args[1].kwargs["json"]["state"] == ModelStates.FAILED.value
        assert call_args[1].kwargs["json"]["result"] == {}
"""
