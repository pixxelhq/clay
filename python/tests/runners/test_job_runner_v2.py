# type: ignore
import copy
import json
import os
import pathlib
import shutil
import unittest
from typing import Any
from unittest.mock import patch  # noqa

import datatypes
import shortuuid

from clay import types
from clay.core import ModelWrapper
from clay.logger import Logger
from clay.runners.job_runner_v2 import JobRunnerV2, _ArgoConfEnvVars, _InjectedEnvVars

# mocking `_upload_parameter_output_spec_file` for tests
JobRunnerV2._upload_parameter_output_spec_file = lambda self, data_item_name, local_spec_file_path: None


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
        self.raster = {
            "format": "raster",
            "name": "raster",
            "type": "url",
            "value": "s3://bucket/another-bucket/clipped.tiff",
            "properties": {
                "bands": ["A", "B", "C"],
                "source": "some-source",
                "collection": "some-collection",
                "dtype": "some-dtype",
            },
        }

        # creating a dummy string input
        self.string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        # creating dummy inputs
        raster_path = os.path.join(input_working_dir, "raster")
        os.mkdir(raster_path)
        with open(os.path.join(raster_path, "spec.json"), "w+") as f:
            json.dump(self.raster, f)

        # string_path = os.path.join(input_working_dir, "string")
        # os.mkdir(string_path)
        # with open(os.path.join(string_path, "spec.json"), "w+") as f:
        #    json.dump(string, f)

        self.mock_env_vars = {
            _InjectedEnvVars.TaskId.value: "task123",
            _InjectedEnvVars.WorkingDir.value: self.testing_working_dir,
            _InjectedEnvVars.InputsWorkingDir.value: input_working_dir,
            _InjectedEnvVars.InputsRemotePath.value: "",
            _InjectedEnvVars.OutputsWorkingDir.value: output_working_dir,
            _InjectedEnvVars.OutputsRemotePath.value: "s3://workflow-id/job-id/task-id/outputs/",  # noqa
            _InjectedEnvVars.Env.value: "local",
            _ArgoConfEnvVars.ArgoTemplate.value: '{"inputs": {"parameters":[{"name": "string", "value":"hello world"}]}}',
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.testing_working_dir)

    async def test_read_inputs(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster) -> Any:
                print(string, raster)
                return {"raster": raster, "string": string.Value}

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

        assert passed_vals["raster"] == os.path.join(self.testing_working_dir, "inputs", "raster", "clipped.tiff")
        assert passed_vals["string"] == "hello world"
        env_patcher.stop()

    async def test_set_outputs(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
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
                    "result": types.Raster(name="result", value=raster),
                    "string": types.String(name="string", value=string.Value),
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

        inputs_list = a.get_inputs_list()
        assert inputs_list[0] == self.raster

        target_raster_asset_path = os.path.join(self.testing_working_dir, "outputs", "raster_group", "result", "clipped.tiff")
        target_raster_spec_path = os.path.join(self.testing_working_dir, "outputs", "raster_group", "result", "spec.json")
        target_string_spec_path = os.path.join(self.testing_working_dir, "outputs", "string", "spec.json")
        assert os.path.exists(target_raster_asset_path)
        assert os.path.exists(target_raster_spec_path)
        assert os.path.exists(target_string_spec_path)

    async def test_set_output_with_custom_properties(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
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
                        is_artifact=True,
                        properties=types.RasterProperties(
                            Bands=["B10"],
                            Source="a-random-sat",
                            Collection="a-random-coll",
                            Dtype="uint8",
                            SunElevation=5.1,
                            Date="20-04-2024",
                        ),
                    ),
                    "string": types.String(name="string", value="hello world", parameter=True),
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

        target_raster_asset_path = os.path.join(self.testing_working_dir, "outputs", "result", "clipped.tiff")
        target_raster_spec_path = os.path.join(self.testing_working_dir, "outputs", "result", "spec.json")

        assert os.path.exists(target_raster_asset_path)
        assert os.path.exists(target_raster_spec_path)

        with open(target_raster_spec_path) as f:
            d = json.load(f)

        assert d == {
            "format": "raster",
            "type": "url",
            "name": "result",
            "display_name": "",
            "description": "",
            "value": "s3://workflow-id/job-id/task-id/outputs/result/clipped.tiff",
            "is_artifact": True,
            "metadata": {},
            "group": "",
            "default": None,
            "properties": {
                "bands": ["B10"],
                "source": "a-random-sat",
                "collection": "a-random-coll",
                "dtype": "uint8",
                "sun_elevation": 5.1,
                "satellite_look_angle": None,
                "discretization": None,
                "visualisation": None,
                "date": "20-04-2024",
                "images": None,
            },
        }

    async def test_set_output_with_autopopulated_metadata(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
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
                        is_artifact=True,
                    ),
                    "string": types.String(name="string", value="hello world", parameter=True),
                }

        env_list = self.mock_env_vars
        env_list["BLOCK_NAME"] = "test-artifact"
        env_patcher = unittest.mock.patch.dict(os.environ, env_list)
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

        target_raster_asset_path = os.path.join(self.testing_working_dir, "outputs", "result", "clipped.tiff")
        target_raster_spec_path = os.path.join(self.testing_working_dir, "outputs", "result", "spec.json")

        assert os.path.exists(target_raster_asset_path)
        assert os.path.exists(target_raster_spec_path)

        with open(target_raster_spec_path) as f:
            d = json.load(f)

        assert d == {
            "format": "raster",
            "type": "url",
            "name": "result",
            "display_name": "",
            "description": "",
            "value": "s3://workflow-id/job-id/task-id/outputs/result/clipped.tiff",
            "is_artifact": True,
            "metadata": {"block-name": "test-artifact"},
            "default": None,
            "group": "",
            "properties": {
                "bands": ["B10"],
                "source": "a-random-sat",
                "collection": "a-random-coll",
                "dtype": "uint8",
                "sun_elevation": 0.0,
                "satellite_look_angle": 0.0,
                "discretization": None,
                "visualisation": None,
                "images": [],
                "date": "",
            },
        }

    async def test_set_output_props_when_not_expected_fails(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
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
                            Date="20-04-2024",
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


class TestJobRunnerV2_WithTypesV2(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        # truncating is fine since this is anyway a tmp directory
        self.testing_working_dir = f"./tmp-{shortuuid.random()[:5]}"
        os.mkdir(self.testing_working_dir)
        input_working_dir = os.path.join(self.testing_working_dir, "inputs")
        output_working_dir = os.path.join(self.testing_working_dir, "outputs")
        os.mkdir(input_working_dir)
        # os.mkdir(output_working_dir)

        # creating a raster dummy input
        self.raster = {
            "format": "raster",
            "name": "raster",
            "type": "url",
            "value": "s3://bucket/another-bucket/clipped.tiff",
            "properties": {
                "bands": ["A", "B", "C"],
                "source": "some-source",
                "collection": "some-collection",
                "dtype": "some-dtype",
            },
        }

        # creating a dummy string input
        self.string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        # creating dummy inputs
        raster_path = os.path.join(input_working_dir, "raster")
        os.mkdir(raster_path)
        with open(os.path.join(raster_path, "spec.json"), "w+") as f:
            json.dump(self.raster, f)

        # string_path = os.path.join(input_working_dir, "string")
        # os.mkdir(string_path)
        # with open(os.path.join(string_path, "spec.json"), "w+") as f:
        #    json.dump(string, f)

        self.mock_env_vars = {
            _InjectedEnvVars.TaskId.value: "task123",
            _InjectedEnvVars.WorkingDir.value: self.testing_working_dir,
            _InjectedEnvVars.InputsWorkingDir.value: input_working_dir,
            _InjectedEnvVars.InputsRemotePath.value: "",
            _InjectedEnvVars.OutputsWorkingDir.value: output_working_dir,
            _InjectedEnvVars.OutputsRemotePath.value: "s3://workflow-id/job-id/task-id/outputs/",  # noqa
            _InjectedEnvVars.Env.value: "local",
            _ArgoConfEnvVars.ArgoTemplate.value: '{"inputs": {"parameters":[{"name": "string", "value":"hello world"}]}}',
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.testing_working_dir)

    async def test_types_v2_read_inputs_with_only_forced_inputs_conversion(self):
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster) -> Any:
                assert isinstance(string, datatypes.String)
                assert isinstance(raster, datatypes.Raster)
                print(string, raster)
                return {"raster": raster.value, "string": string.value}

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

        env_dict = copy.deepcopy(self.mock_env_vars)
        env_dict["FEATURE_ENABLE_TYPES_V2"] = "1"
        env_dict["FEATURE_FORCE_INPUT_TYPES_TO_V2"] = "1"

        env_patcher = unittest.mock.patch.dict(os.environ, env_dict)
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

        assert passed_vals["raster"] == os.path.join(self.testing_working_dir, "inputs", "raster", "clipped.tiff")
        assert passed_vals["string"] == "hello world"
        env_patcher.stop()

    async def test_types_v2_outputs_with_only_forced_output_conversion(self) -> None:
        class M(ModelWrapper):
            def __init__(
                self,
                config: str,
                protocol: str = "s3fs",
                logger=None,
            ) -> None:
                super().__init__(config, protocol, logger)

            def setup(self) -> None:
                pass

            async def preprocess(self, raster: types.Raster, string: types.String) -> Any:
                assert isinstance(raster, types.Raster)
                assert isinstance(string, types.String)
                print(raster.Value, string.Value)
                return {"x": 123}

            async def inference(self, x: int) -> Any:
                return {"y": x + 1}

            async def postprocess(self, y) -> None:
                return {"z": types.Number(name="z", value=y + 1, type="str")}

        env_dict = copy.deepcopy(self.mock_env_vars)
        env_dict["FEATURE_ENABLE_TYPES_V2"] = "1"
        env_dict["FEATURE_FORCE_OUTPUT_TYPES_TO_V2"] = "1"

        env_patcher = unittest.mock.patch.dict(os.environ, env_dict)
        env_patcher.start()
        a = JobRunnerV2(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec-3.yml"},
            "./tests/runners/dummy-spec-3.yml",
            None,
        )
        a.start()
        env_patcher.stop()

        target_result_spec_path = os.path.join(
            self.testing_working_dir,
            "outputs",
            "number_group",
            "z",
            "spec.json",
        )

        assert os.path.exists(target_result_spec_path)
        with open(target_result_spec_path) as f:
            d = json.load(f)
        assert d["version"] == "v2"

    async def test_model_accepts_and_produces_proto_but_output_proto_gets_converted_v1(self):
        class M(ModelWrapper):
            def __init__(
                self,
                config: str,
                protocol: str = "s3fs",
                logger=None,
            ) -> None:
                super().__init__(config, protocol, logger)

            def setup(self) -> None:
                pass

            async def preprocess(self, raster: datatypes.Raster, string: datatypes.String) -> Any:
                assert isinstance(raster, datatypes.Raster)
                assert isinstance(string, datatypes.String)
                print(raster.value, string.value)
                return {"x": 123}

            async def inference(self, x: int) -> Any:
                return {"y": x + 1}

            async def postprocess(self, y) -> None:
                return {"z": datatypes.Number(format=datatypes.Format.number, name="z", value=str(y + 1), type="str")}

        env_dict = copy.deepcopy(self.mock_env_vars)
        env_dict["FEATURE_FORCE_INPUT_TYPES_TO_V2"] = "1"
        env_dict["FEATURE_FORCE_OUTPUT_TYPES_TO_V2"] = "0"

        env_patcher = unittest.mock.patch.dict(os.environ, env_dict)
        env_patcher.start()
        a = JobRunnerV2(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec-3.yml"},
            "./tests/runners/dummy-spec-3.yml",
            None,
        )
        a.start()
        env_patcher.stop()

        target_result_spec_path = os.path.join(
            self.testing_working_dir,
            "outputs",
            "number_group",
            "z",
            "spec.json",
        )

        assert os.path.exists(target_result_spec_path)
        with open(target_result_spec_path) as f:
            d = json.load(f)
        assert "version" not in d
