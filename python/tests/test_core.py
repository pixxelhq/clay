import json
import os
import pathlib
import shutil
import sys
import time
import unittest
from typing import Any
from unittest import mock

import pytest
import shortuuid

from clay import ModelWrapper
from clay.core import BaseRunner
from clay.exceptions import OutputOverwriteException
from clay.logger import Logger
from clay.types import RasterProperties

from .models.ymxplusc import YMXPLUSC, YMXPLUSC_CONFIG, make_ymxplusc_input

sys.path.append("./tests/testrepo")


def test_mw_missing_setup_override() -> None:
    class M(ModelWrapper):
        async def preprocess(self, *args: Any, **kwargs: Any) -> Any:
            pass

    with pytest.raises(NotImplementedError):
        M(config="tests/models/ymxplusc.yaml")


def test_mw_blocking_method_override() -> None:
    with pytest.raises(AssertionError):

        class M(ModelWrapper):
            def setup(self) -> None:
                pass

            def preprocess(self, *args: Any, **kwargs: Any) -> Any:
                pass


def test_mw_parse_inputs(toy_model) -> None:
    # sanity check - all params succesfully created
    model_input = json.loads(make_ymxplusc_input())[1:]
    parsed_input = toy_model._parse_inputs(model_input)
    for param in toy_model.config.inputs:
        assert param["name"] in parsed_input.keys()
    # TODO: write better test


@pytest.mark.asyncio
async def test_mw_model_inference(toy_model) -> None:
    # TODO: Write better test
    model_inputs = json.loads(make_ymxplusc_input())[1:]
    result = await toy_model.infer(model_inputs)
    assert isinstance(result[0]["value"], float)
    assert isinstance(result[1]["value"], str)


class TestModelWrapper(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        # truncating is fine since this is anyway a tmp directory
        self.testing_working_dir = f"./tmp-{shortuuid.random()[:5]}"
        os.mkdir(self.testing_working_dir)
        input_working_dir = os.path.join(self.testing_working_dir, "inputs")
        output_working_dir = os.path.join(self.testing_working_dir, "outputs")
        os.mkdir(input_working_dir)
        # os.mkdir(output_working_dir)

        # creating a raster dummy input
        raster = {
            "format": "raster",
            "type": "url",
            "value": "s3://bucket/another-bucket/clipped.tiff",
            "properties": {},
        }

        # creating a dummy string input
        string = {"format": "string", "type": "str", "value": "hello world"}

        # creating dummy inputs
        raster_path = os.path.join(input_working_dir, "raster")
        os.mkdir(raster_path)
        with open(os.path.join(raster_path, "spec.json"), "w+") as f:
            json.dump(raster, f)

        string_path = os.path.join(input_working_dir, "string")
        os.mkdir(string_path)
        with open(os.path.join(string_path, "spec.json"), "w+") as f:
            json.dump(string, f)

        self.mock_env_vars = {
            "task-id": "task123",
            "working-dir": self.testing_working_dir,
            "inputs-working-dir": input_working_dir,
            "outputs-working-dir": output_working_dir,
            "outputs-remote-path": "s3://workflow-id/job-id/task-id/outputs/",
            "env": "local",
        }

        class M(ModelWrapper):
            def __init__(
                self, config: str, protocol: str = "abfs", logger: Logger = None
            ) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster) -> Any:
                print(string, raster)
                return {"raster": raster, "string": string}

            async def inference(self, raster, string) -> None:
                return {"raster": raster, "string": string}

            async def postprocess(self, raster, string) -> Any:
                return raster, string

        self._m = M

    def tearDown(self) -> None:
        shutil.rmtree(self.testing_working_dir)

    async def test_read_inputs(self) -> None:
        env_patcher = mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        _m = self._m("./python/tests/dummy-spec.yml", "s3", None)
        raster, string = await _m.infer(None)
        assert raster == os.path.join(
            self.testing_working_dir, "inputs", "raster", "clipped.tiff"
        )
        assert string == "hello world"
        env_patcher.stop()

    async def test_set_outputs(self) -> None:
        class M(ModelWrapper):
            def __init__(
                self, config: str, protocol: str = "abfs", logger: Logger = None
            ) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster) -> Any:
                print(string, raster)
                return {"raster": raster, "string": string}

            async def inference(self, raster, string) -> None:
                dummy_raster = pathlib.Path("clipped.tiff")
                dummy_raster.touch()
                return {"raster": str(dummy_raster), "string": string}

            async def postprocess(self, raster, string) -> Any:
                self.output("result", raster)
                self.output("string", string)
                return raster, string

        env_patcher = mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        print(os.getcwd())
        _m = M("./python/tests/dummy-spec.yml", "s3", None)
        raster, string = await _m.infer(None)
        env_patcher.stop()

        target_raster_asset_path = os.path.join(
            self.testing_working_dir, "outputs", "result", "clipped.tiff"
        )
        target_raster_spec_path = os.path.join(
            self.testing_working_dir, "outputs", "result", "spec.json"
        )
        target_string_spec_path = os.path.join(
            self.testing_working_dir, "outputs", "string", "spec.json"
        )

        assert os.path.exists(target_raster_asset_path)
        assert os.path.exists(target_raster_spec_path)
        assert os.path.exists(target_string_spec_path)

    async def test_set_output_with_custom_properties(self) -> None:
        class M(ModelWrapper):
            def __init__(
                self, config: str, protocol: str = "abfs", logger: Logger = None
            ) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster) -> Any:
                print(string, raster)
                return {"raster": raster, "string": string}

            async def inference(self, raster, string) -> None:
                dummy_raster = pathlib.Path("clipped.tiff")
                dummy_raster.touch()
                return {"raster": str(dummy_raster), "string": string}

            async def postprocess(self, raster, string) -> Any:
                self.output(
                    "result",
                    raster,
                    RasterProperties(
                        Bands=["B10"],
                        Source="a-random-sat",
                        Collection="a-random-coll",
                        Dtype="uint8",
                    ),
                )
                self.output("string", string)
                return raster, string

        env_patcher = mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        _m = M("./python/tests/dummy-spec.yml", "s3", None)
        raster, string = await _m.infer(None)
        env_patcher.stop()

        target_raster_asset_path = os.path.join(
            self.testing_working_dir, "outputs", "result", "clipped.tiff"
        )
        target_raster_spec_path = os.path.join(
            self.testing_working_dir, "outputs", "result", "spec.json"
        )

        assert os.path.exists(target_raster_asset_path)
        assert os.path.exists(target_raster_spec_path)

        with open(target_raster_spec_path) as f:
            d = json.load(f)

        assert d == {
            "format": "raster",
            "type": "url",
            "name": "result",
            "value": "s3://workflow-id/job-id/task-id/outputs/result/clipped.tiff",
            "properties": {
                "bands": ["B10"],
                "source": "a-random-sat",
                "collection": "a-random-coll",
                "dtype": "uint8",
            },
        }

    async def test_set_output_duplicate_fails(self) -> None:
        class M(ModelWrapper):
            def __init__(
                self, config: str, protocol: str = "abfs", logger: Logger = None
            ) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster) -> Any:
                print(string, raster)
                return {"raster": raster, "string": string}

            async def inference(self, raster, string) -> None:
                dummy_raster = pathlib.Path("clipped.tiff")
                dummy_raster.touch()
                return {"raster": str(dummy_raster), "string": string}

            async def postprocess(self, raster, string) -> Any:
                self.output("string", string)
                self.output("string", string)
                return raster, string

        env_patcher = mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        with pytest.raises(OutputOverwriteException):
            _m = M("./python/tests/dummy-spec.yml", "s3", None)
            raster, string = await _m.infer(None)
        env_patcher.stop()


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
