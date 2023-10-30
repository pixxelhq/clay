import os
import sys
import time
import unittest
from typing import Any
from unittest import mock

import pytest

from clay import ModelWrapper, types
from clay.core import BaseRunner

from .models.ymxplusc import YMXPLUSC, YMXPLUSC_CONFIG

sys.path.append("./tests/testrepo")


def test_mw_missing_setup_override() -> None:
    class M(ModelWrapper):
        async def preprocess(self, *args: Any, **kwargs: Any) -> Any:
            pass

    with pytest.raises(NotImplementedError):
        M(config="./python/tests/models/ymxplusc.yaml")


def test_mw_blocking_method_override() -> None:
    with pytest.raises(AssertionError):

        class M(ModelWrapper):
            def setup(self) -> None:
                pass

            def preprocess(self, *args: Any, **kwargs: Any) -> Any:
                pass


class TestBaseRunner(unittest.TestCase):
    def setUp(self) -> None:
        class M(ModelWrapper):
            def setup(self, a: str, x: list):
                pass

            async def preprocess(self, i: str) -> Any:
                return 1, 2, {"a": 123}

            async def postprocess(self) -> Any:
                pass

        class DemoRunner(BaseRunner):
            def __init__(self, run_mode: str):
                super().__init__(
                    run_mode=run_mode,
                    modelcls=YMXPLUSC,
                    model_args={"config": YMXPLUSC_CONFIG},
                    logger=None,
                    cfg_path=YMXPLUSC_CONFIG,
                )

        self._test_modelcls = YMXPLUSC
        self._test_runnercls = DemoRunner

    def tearDown(self) -> None:
        if hasattr(self, "m") and hasattr(self.m, "_loop"):
            if self.m._loop.is_running():
                self.m._loop.call_soon_threadsafe(self.m._loop.stop)
                time.sleep(3)
            assert self.m._loop.is_running() is False
            self.m._loop.close()

        time.sleep(1)

    def test_invalid_runner_mode(self):
        with pytest.raises(ValueError):
            self._test_runnercls("test")

    def test_model_init(self):
        self.m = self._test_runnercls("job")
        self.m._init_model()
        assert isinstance(self.m._model, self._test_modelcls)

    def test_model_inference_close_event_loop(self):
        self.m = self._test_runnercls("job")
        self.m._init_model()
        self.m._init_model_inference_event_loop()
        assert self.m._loop.is_running() is True

        self.m._loop.call_soon_threadsafe(self.m._loop.stop)

        time.sleep(2)

        assert self.m._loop.is_running() is False
        assert self.m._t.is_alive() is False

    def test_model_inference_thread_init(self):
        # BIG NOTE: this test fails for some reason when
        # clay/core.py:L63 is set to `asyncio.get_event_loop` instead of
        # `asyncio.new_event_loop` even though in both cases, the class works
        # fine outside of test. `new_event_loop` may potentially cause problems
        # in environments with pre-existing event loops like uvicorn server.
        self.m = self._test_runnercls("job")
        self.m._init_model()
        self.m._init_model_inference_event_loop()
        assert self.m._t.is_alive() is True

    def test_model_inference_event_loop_init(self):
        # BIG NOTE: this test fails for some reason when
        # clay/core.py:L63 is set to `asyncio.get_event_loop` instead of
        # `asyncio.new_event_loop` even though in both cases, the class works
        # fine outside of test. `new_event_loop` may potentially cause problems
        # in environments with pre-existing event loops like uvicorn server.
        self.m = self._test_runnercls("job")
        self.m._init_model()
        self.m._init_model_inference_event_loop()
        assert self.m._loop.is_running() is True

    @mock.patch("clay.core.requests.Session.post")
    def test_fire_callback_workflow_success(self, mock_post):
        mock_response = mock.Mock()
        mock_response.json.return_value = {"successful_update": "True", "err": ""}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        dexter_url = "localhost:6666"
        mock_env_vars = {
            "DEXTER_RUN_TYPE": "workflow",
            "ORCHESTRATOR_URL": dexter_url,
            "DEXTER_CLB_AUTH_TOKEN": "123",
        }
        env_patcher = unittest.mock.patch.dict(os.environ, mock_env_vars)
        env_patcher.start()
        self.m = self._test_runnercls("job")
        self.m._init_model()
        self.m._init_model_inference_event_loop()
        self.m._fire_callback(
            types.Callback(Id="task123", State=types.ModelStates.INPROGRESS)
        )
        call_args = mock_post.call_args_list
        assert call_args[0][1]["url"] == dexter_url
        env_patcher.stop()

    @mock.patch("clay.core.requests.Session.post")
    def test_fire_callback_inference_success(self, mock_post):
        mock_response = mock.Mock()
        mock_response.json.return_value = {"successful_update": "True", "err": ""}
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        dexter_url = "http://localhost:6666/v1alpha1/inferences/task123"
        mock_env_vars = {
            "DEXTER_RUN_TYPE": "inference",
            "ORCHESTRATOR_URL": dexter_url,
            "DEXTER_CLB_AUTH_TOKEN": "123",
            "DEXTER_HOST": "http://localhost",
            "DEXTER_PORT": "6666",
        }
        env_patcher = unittest.mock.patch.dict(os.environ, mock_env_vars)
        env_patcher.start()
        self.m = self._test_runnercls("job")
        self.m._init_model()
        self.m._init_model_inference_event_loop()
        self.m._fire_callback(
            types.Callback(Id="task123", State=types.ModelStates.FAILED)
        )
        call_args = mock_post.call_args_list
        assert call_args[0][1]["url"] == dexter_url
        env_patcher.stop()
