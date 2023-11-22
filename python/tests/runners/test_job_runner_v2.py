import json
import os
import pathlib
import shutil
import unittest
from typing import Any

import shortuuid

from clay import types
from clay.core import ModelWrapper
from clay.logger import Logger
from clay.runners.job_runner_v2 import JobRunnerV2


class TestJobRunnerV2(unittest.IsolatedAsyncioTestCase):
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
        string = {"format": "string", "type": "str", "value": "hello world"}  # noqa

        # creating dummy inputs
        raster_path = os.path.join(input_working_dir, "raster")
        os.mkdir(raster_path)
        with open(os.path.join(raster_path, "spec.json"), "w+") as f:
            json.dump(raster, f)

        # string_path = os.path.join(input_working_dir, "string")
        # os.mkdir(string_path)
        # with open(os.path.join(string_path, "spec.json"), "w+") as f:
        #    json.dump(string, f)

        self.mock_env_vars = {
            "task-id": "task123",
            "working-dir": self.testing_working_dir,
            "inputs-working-dir": input_working_dir,
            "outputs-working-dir": output_working_dir,
            "outputs-remote-path": "s3://workflow-id/job-id/task-id/outputs/",
            "env": "local",
            "ARGO_TEMPLATE": '{"inputs": {"parameters":[{"name": "string", "value":"hello world"}]}}',  # noqa
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.testing_working_dir)

    async def test_read_inputs(self) -> None:
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
                return {
                    "result": types.Raster(
                        name="result",
                        value=raster,
                    ),
                    "string": types.String(name=string, value=string),
                }

        env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        a = JobRunnerV2(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec.yml"},
            "./tests/runners/dummy-spec.yml",
            None,
        )
        a.start()
        passed_vals = a.get_passed_inputs_dict()

        assert passed_vals["raster"] == os.path.join(
            self.testing_working_dir, "inputs", "raster", "clipped.tiff"
        )
        assert passed_vals["string"] == "hello world"
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
                print(string)
                return {
                    "result": types.Raster(name="result", value=raster, parameter=True),
                    "string": types.String(
                        name="string", value=string.Value, parameter=True
                    ),
                }

        env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        print(os.getcwd())
        a = JobRunnerV2(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec.yml"},
            "./tests/runners/dummy-spec.yml",
            None,
        )
        a.start()

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

            async def preprocess(self, string: types.String, raster: types.Raster) -> Any:
                print(string, raster)
                return {"raster": raster, "string": string}

            async def inference(self, raster, string) -> None:
                dummy_raster = pathlib.Path("clipped.tiff")
                dummy_raster.touch()
                return {"raster": str(dummy_raster), "string": string}

            async def postprocess(self, raster, string) -> Any:
                return {
                    "result": types.Raster(
                        name="result",
                        value=raster,
                        persistent=True,
                        properties=types.RasterProperties(
                            Bands=["B10"],
                            Source="a-random-sat",
                            Collection="a-random-coll",
                            Dtype="uint8",
                        ),
                    ),
                    "string": types.String(
                        name="string", value="hello world", parameter=True
                    ),
                }

        env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        a = JobRunnerV2(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec-with-props.yml"},
            "./tests/runners/dummy-spec-with-props.yml",
            None,
        )
        a.start()

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
            "persistent": True,
            "default": None,
            "parameter": False,
            "properties": {
                "bands": ["B10"],
                "source": "a-random-sat",
                "collection": "a-random-coll",
                "dtype": "uint8",
            },
        }

    async def test_set_output_props_when_not_expected_fails(self) -> None:
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
                return {
                    "result": types.Raster(
                        name="result",
                        value=raster,
                        properties=types.RasterProperties(
                            Bands=["B10"],
                            Source="a-random-sat",
                            Collection="a-random-coll",
                            Dtype="uint8",
                        ),
                    ),
                    "string": types.String(name="string", value="hello world"),
                }

        env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        a = JobRunnerV2(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec.yml"},
            "./tests/runners/dummy-spec.yml",
            None,
        )
        self.assertRaises(ValueError, a.start)

        env_patcher.stop()
