import os
import sys
import time
import unittest
from typing import Any

import pytest

from clay import ModelWrapper
from clay._network import HeaderBuilder
from clay.core import BaseRunner, CallbackAuthMethod

from .models.ymxplusc import YMXPLUSC, YMXPLUSC_CONFIG
from .utils import set_envvar

sys.path.append("./tests/testrepo")


def test_mw_missing_setup_override() -> None:
    class M(ModelWrapper):
        async def preprocess(self, *args: Any, **kwargs: Any) -> Any:
            pass

    with pytest.raises(NotImplementedError):
        M(config="./tests/models/ymxplusc.yaml")


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
        if hasattr(self, "m") and hasattr(self.r, "_loop"):
            if self.r._loop.is_running():
                self.r._loop.call_soon_threadsafe(self.r._loop.stop)
                time.sleep(3)
            assert self.r._loop.is_running() is False
            self.r._loop.close()

        time.sleep(1)

    def test_invalid_runner_mode(self):
        with pytest.raises(ValueError):
            self._test_runnercls("test")

    def test_model_init(self):
        self.r = self._test_runnercls("job")
        self.r._init_model()
        assert isinstance(self.r._model, self._test_modelcls)

    def test_model_inference_close_event_loop(self):
        self.r = self._test_runnercls("job")
        self.r._init_model()
        self.r._init_model_inference_event_loop()
        assert self.r._loop.is_running() is True

        self.r._loop.call_soon_threadsafe(self.r._loop.stop)

        time.sleep(2)

        assert self.r._loop.is_running() is False
        assert self.r._t.is_alive() is False

    def test_model_inference_thread_init(self):
        # BIG NOTE: this test fails for some reason when
        # clay/core.py:L63 is set to `asyncio.get_event_loop` instead of
        # `asyncio.new_event_loop` even though in both cases, the class works
        # fine outside of test. `new_event_loop` may potentially cause problems
        # in environments with pre-existing event loops like uvicorn server.
        self.r = self._test_runnercls("job")
        self.r._init_model()
        self.r._init_model_inference_event_loop()
        assert self.r._t.is_alive() is True

    def test_model_inference_event_loop_init(self):
        # BIG NOTE: this test fails for some reason when
        # clay/core.py:L63 is set to `asyncio.get_event_loop` instead of
        # `asyncio.new_event_loop` even though in both cases, the class works
        # fine outside of test. `new_event_loop` may potentially cause problems
        # in environments with pre-existing event loops like uvicorn server.
        self.r = self._test_runnercls("job")
        self.r._init_model()
        self.r._init_model_inference_event_loop()
        assert self.r._loop.is_running() is True

    def test_progress_update(self):
        self.r = self._test_runnercls("job")
        self.r._init_model()
        self.r._init_model_inference_event_loop()

        self.r._model._set_progress(13)
        assert self.r._model.get_progress() == 13

        self.r._model._set_progress(13)
        assert self.r._model.get_progress() == 26

        self.r._model._set_progress(5)
        assert self.r._model.get_progress() == 31

        self.r._model._set_progress(100)
        assert self.r._model.get_progress() == 100

    def test_progress_update_with_multiple_increments_greater_than_max(self):
        self.r = self._test_runnercls("job")
        self.r._init_model()
        self.r._init_model_inference_event_loop()

        self.r._model._set_progress(100)
        assert self.r._model.get_progress() == 100

        self.r._model._set_progress(13)
        assert self.r._model.get_progress() == 100

    def test_progress_update_with_negative_increment(self):
        self.r = self._test_runnercls("job")
        self.r._init_model()
        self.r._init_model_inference_event_loop()

        assert self.r._model.get_progress() == 0
        self.r._model._set_progress(-10)
        assert self.r._model.get_progress() == 0


def test_callback_auth_method_init() -> None:
    with set_envvar("DEXTER_CALLBACK_AUTH", "0"):
        assert CallbackAuthMethod.get_method() == CallbackAuthMethod.STATIC_TOKEN
    with set_envvar("DEXTER_CALLBACK_AUTH", "1"):
        assert CallbackAuthMethod.get_method() == CallbackAuthMethod.JWT_TOKEN
    with set_envvar("DEXTER_CALLBACK_AUTH", "2"):
        assert CallbackAuthMethod.get_method() == CallbackAuthMethod.GATEWAY_TOKEN
    with set_envvar("DEXTER_CALLBACK_AUTH", "3"):
        assert CallbackAuthMethod.get_method() == CallbackAuthMethod.NO_AUTH
    assert CallbackAuthMethod.get_method() == CallbackAuthMethod.NO_AUTH


class TestHeaderBuilder(unittest.TestCase):
    def test_init_static_token_auth(self) -> None:
        with set_envvar("DEXTER_CALLBACK_AUTH", "0"):
            os.environ["DEXTER_CLB_AUTH_TOKEN"] = "123"
            header = HeaderBuilder.init_header()
            assert "Authorization" in header
            assert header["Authorization"] == "Token 123"

    def test_init_jwt_auth(self) -> None:
        with set_envvar("DEXTER_CALLBACK_AUTH", "1"):
            os.environ["DEXTER_CLB_AUTH_TOKEN"] = "456"
            header = HeaderBuilder.init_header()
            assert "Authorization" in header
            assert header["Authorization"] == "Bearer 456"

    def test_init_gateway_auth(self) -> None:
        with set_envvar("DEXTER_CALLBACK_AUTH", "2"):
            os.environ["DEXTER_GATEWAY_SUB"] = "123"
            os.environ["DEXTER_GATEWAY_ORGIDS"] = "456"
            header = HeaderBuilder.init_header()
            assert header["X-AuthService-Sub"] == "123"
            assert header["X-AuthService-Org_Ids"] == "456"
