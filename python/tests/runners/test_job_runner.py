# type: ignore
import copy
import json
import os
import pathlib
import shutil
import unittest
from typing import Any
from unittest.mock import patch  # noqa

import pytest
import shortuuid

from clay import types
from clay.core import ModelWrapper
from clay.logger import Logger
from clay.runners.job_runner import JobRunner, _ExpectedInfParameters

pytest.importorskip("test_job_runner")


class TestJobRunner(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        # truncating is fine since this is anyway a tmp directory
        self.testing_working_dir = f"tmp-{shortuuid.random()[:5]}"
        os.mkdir(self.testing_working_dir)
        input_working_dir = os.path.join(self.testing_working_dir, "inputs")
        output_working_dir = os.path.join(self.testing_working_dir, "outputs")
        os.mkdir(input_working_dir)
        # os.mkdir(output_working_dir)

        # creating dummy inputs
        self.mock_env_vars = {
            "task-id": "task123",
            "job-id": "job123",
            "workflow-id": "wfk123",
            "local-working-dir": self.testing_working_dir,
            "working-dir": self.testing_working_dir,
            "inputs-working-dir": input_working_dir,
            "outputs-working-dir": output_working_dir,
            "REMOTE_PREFIX":"insights",
            "outputs-remote-path": "s3://workflow-id/job-id/task-id/outputs/",
            "env": "local",
            "AWS_PROFILE": "d-platform-services",
            "DISABLE_AUTO_UPLOAD": "false",
            "AUTO_DOWNLOAD_ASSETS": "false",
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
                return {"raster": raster, "string": string}

            async def inference(self, raster, string) -> None:
                dummy_raster = pathlib.Path("../clipped.tiff")
                dummy_raster.touch()

                return {"raster": str(dummy_raster), "string": "this is hello"}

            async def postprocess(self, raster, string) -> Any:
                r = types.Raster(
                    name="result",
                    value=raster,
                )
                s = types.String(name="string", value=string)
                return {
                    "result": r,
                    "string": s,
                }

        # creating a raster dummy input
        raster = {
            "format": "raster",
            "type": "url",
            "name": "raster",
            "stac_url": "stac",
            "value": "s3://bucket/another-bucket/clipped.tiff",
        }

        # creating a dummy string input
        string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        a = JobRunner(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec.yml"},
            "./tests/runners/dummy-spec.yml",
            None,
        )
        a.start(args=[raster, string])
        passed_vals = a.get_passed_inputs_dict()

        assert passed_vals["raster"]["value"] == raster["value"]
        assert passed_vals["string"]["value"] == "hello world"
        env_patcher.stop()

    async def test_set_outputs(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster) -> Any:
                print(string, raster)
                filepath = pathlib.Path("../clipped.tiff")
                self.add_asset(file_path=filepath, io_name=raster) 
                return {"raster": raster, "string": string}

            async def inference(self, raster, string) -> None:
                dummy_raster = pathlib.Path("../clipped.tiff")
                dummy_raster.touch()

                return {"raster": str(dummy_raster), "string": "this is hello"}

            async def postprocess(self, raster, string) -> Any:
                r = types.Raster(
                    name="result",
                    value=raster,
                )
                s = types.String(name="string", value=string)
                return {
                    "result": r,
                    "string": s,
                }

        # creating a raster dummy input
        raster = {
            "format": "raster",
            "type": "url",
            "name": "raster",
            "stac_url": "stac",
            "value": "s3://bucket/another-bucket/clipped.tiff",
        }

        # creating a dummy string input
        string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        a = JobRunner(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec.yml"},
            "./tests/runners/dummy-spec.yml",
            None,
        )
        a.start(args=[raster, string])
        passed_vals = a.get_passed_inputs_dict()

        assert passed_vals["raster"]["value"] == raster["value"]
        assert passed_vals["string"]["value"] == "hello world"
        env_patcher.stop()

        target_raster_asset_path = os.path.join(
            self.testing_working_dir,
            "wfk123",
            "job123",
            "task123",
            "outputs",
            "result",
            "clipped.tiff",
        )
        target_raster_spec_path = os.path.join(
            self.testing_working_dir,
            "wfk123",
            "job123",
            "task123",
            "outputs",
            "result",
            "spec.json",
        )
        target_string_spec_path = os.path.join(
            self.testing_working_dir,
            "wfk123",
            "job123",
            "task123",
            "outputs",
            "string",
            "spec.json",
        )
        target_added_asset_path = os.path.join("insights", "wfk123",
            "job123",
            "task123",
            "outputs","result", "clipped.tiff" )

        assert os.path.exists(target_raster_asset_path)
        assert os.path.exists(target_raster_spec_path)
        assert os.path.exists(target_string_spec_path)
        assert os.path.exists(target_added_asset_path)

    async def test_read_inputs_and_download_remote_asset(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster) -> Any:
                print(string, raster)
                return {"raster": raster, "string": string}

            async def inference(self, raster, string) -> None:
                dummy_raster = pathlib.Path("../clipped.tiff")
                dummy_raster.touch()

                return {"raster": str(dummy_raster), "string": "this is hello"}

            async def postprocess(self, raster, string) -> Any:
                r = types.Raster(
                    name="result",
                    value=raster,
                )
                s = types.String(name="string", value=string)
                return {
                    "result": r,
                    "string": s,
                }

        # creating a raster dummy input
        raster = {
            "format": "raster",
            "type": "url",
            "name": "raster",
            "stac_url": "stac",
            "value": "s3://d-platform-orchestrator-lulc-artifacts-s3-01/test-raster.tiff",
        }

        # creating a dummy string input
        string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        mock_env_vars = copy.deepcopy(self.mock_env_vars)
        mock_env_vars["AUTO_DOWNLOAD_ASSETS"] = "true"
        mock_env_vars["REMOTE_PREFIX"] = "s3://d-platform-orchestrator-lulc-artifacts-s3-01"
        env_patcher = unittest.mock.patch.dict(os.environ, mock_env_vars)
        env_patcher.start()
        a = JobRunner(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec.yml"},
            "./tests/runners/dummy-spec.yml",
            None,
        )
        a.start(args=[raster, string])
        env_patcher.stop()
        passed_vals = a.get_passed_inputs_dict()

        raster_input_dir = os.path.join(
            self.testing_working_dir,
            "wfk123",
            "job123",
            "task123",
            "inputs",
            "raster",
        )

        assert os.path.samefile(
            passed_vals["raster"]["value"],
            os.path.join(
                self.testing_working_dir,
                "wfk123",
                "job123",
                "task123",
                "inputs",
                "raster",
                "test-raster.tiff",
            ),
        )
        assert passed_vals["string"]["value"] == "hello world"
        assert os.path.exists(os.path.join(raster_input_dir, "test-raster.tiff"))
        with open(os.path.join(raster_input_dir, "spec.json"), "r") as f:
            d = json.load(f)
        assert os.path.samefile(d["value"], os.path.join(raster_input_dir, "test-raster.tiff"))

    async def test_auto_upload_generated_assets_enabled_success(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster) -> Any:
                print(string, raster)
                return {"raster": raster, "string": string}

            async def inference(self, raster, string) -> None:
                dummy_raster = pathlib.Path("../clipped.tiff")
                dummy_raster.touch()

                return {"raster": str(dummy_raster), "string": "this is hello"}

            async def postprocess(self, raster, string) -> Any:
                r = types.Raster(
                    name="result",
                    value=raster,
                )
                s = types.String(name="string", value=string)
                return {
                    "result": r,
                    "string": s,
                }

        # creating a raster dummy input
        raster = {
            "format": "raster",
            "type": "url",
            "name": "raster",
            "stac_url": "stac",
            "value": "s3://d-platform-orchestrator-lulc-artifacts-s3-01/test-raster.tiff",
        }

        # creating a dummy string input
        string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        mock_env_vars = copy.deepcopy(self.mock_env_vars)
        mock_env_vars["AUTO_DOWNLOAD_ASSETS"] = "true"
        mock_env_vars["REMOTE_PREFIX"] = "s3://d-platform-orchestrator-lulc-artifacts-s3-01"
        mock_env_vars["DISABLE_AUTO_UPLOAD"] = "false"
        mock_env_vars["BLOCK_NAME"] = "test-artifact"
        env_patcher = unittest.mock.patch.dict(os.environ, mock_env_vars)
        env_patcher.start()
        a = JobRunner(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec.yml"},
            "./tests/runners/dummy-spec.yml",
            None,
        )
        a.start(args=[raster, string])
        passed_vals = a.get_passed_inputs_dict()

        result_output_dir = os.path.join(
            self.testing_working_dir,
            "wfk123",
            "job123",
            "task123",
            "outputs",
            "result",
        )
        remote_raster_path = os.path.join(
            "s3://d-platform-orchestrator-lulc-artifacts-s3-01",
            "wfk123",
            "job123",
            "task123",
            "outputs",
            "result",
            "clipped.tiff",
        )

        assert os.path.samefile(
            passed_vals["raster"]["value"],
            os.path.join(
                self.testing_working_dir,
                "wfk123",
                "job123",
                "task123",
                "inputs",
                "raster",
                "test-raster.tiff",
            ),
        )
        assert passed_vals["string"]["value"] == "hello world"
        assert os.path.exists(os.path.join(result_output_dir, "clipped.tiff"))
        with open(os.path.join(result_output_dir, "spec.json"), "r") as f:
            d = json.load(f)
        assert d["value"] == remote_raster_path
        assert d["metadata"] == {"block-name": "test-artifact"}

    async def test_read_inputs_backward_compatible(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster) -> Any:
                print(string, raster)
                return {"raster": raster, "string": string}

            async def inference(self, raster, string) -> None:
                dummy_raster = pathlib.Path("../clipped.tiff")
                dummy_raster.touch()

                return {"raster": str(dummy_raster), "string": "this is hello"}

            async def postprocess(self, raster, string) -> Any:
                r = types.Raster(
                    name="result",
                    value=raster,
                )
                s = types.String(name="string", value=string)
                return {
                    "result": r,
                    "string": s,
                }

        # creating a raster dummy input
        raster = {
            "format": "raster",
            "type": "url",
            "name": "raster",
            "stac_url": "stac",
            "value": "s3://bucket/another-bucket/clipped.tiff",
        }

        # creating a dummy string input
        string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        mock_env_vars = copy.deepcopy(self.mock_env_vars)
        mock_env_vars["local-working-dir"] = self.testing_working_dir
        mock_env_vars["workflow-id"] = "wfk123"
        mock_env_vars["job-id"] = "job123"
        env_patcher = unittest.mock.patch.dict(os.environ, mock_env_vars)
        env_patcher.start()
        a = JobRunner(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec.yml"},
            "./tests/runners/dummy-spec.yml",
            None,
        )
        a.start(args=[raster, string])
        passed_vals = a.get_passed_inputs_dict()

        assert a._inf_opts[_ExpectedInfParameters.WorkflowId] == "wfk123"
        assert a._inf_opts[_ExpectedInfParameters.JobId] == "job123"
        assert a._inf_opts[_ExpectedInfParameters.TaskId] == "task123"

        assert passed_vals["raster"]["value"] == raster["value"]
        assert passed_vals["string"]["value"] == "hello world"

    async def test_handle_input_vector_assets(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, vector_string: types.Vector, vector_file: types.Vector) -> Any:
                print(vector_file, vector_string)
                return {"vector_file": vector_file, "vector_string": vector_string}

            async def inference(self, vector_file, vector_string):
                return {"vector_file": vector_file, "vector_string": vector_string}

            async def postprocess(self, vector_file, vector_string) -> Any:
                s = types.String(name="string", value="hello world")
                return {
                    "string": s,
                }

        # creating a vector dummy input
        vector_file = {
            "format": "vector",
            "type": "url",
            "name": "vector_file",
            "value": "s3://d-platform-orchestrator-lulc-artifacts-s3-01/test_abc.geojson",
        }

        # creating a dummy string input
        vector_string = {
            "format": "vector",
            "type": "url",
            "name": "vector_string",
            "value": '{"type":"Feature","geometry":{"type":"Point","coordinates":[125.6,10.1]},"properties":{"name":"Dinagat Islands"}}',
        }

        mock_env_vars = copy.deepcopy(self.mock_env_vars)
        mock_env_vars["AUTO_DOWNLOAD_ASSETS"] = "true"
        mock_env_vars["REMOTE_PREFIX"] = "s3://d-platform-orchestrator-lulc-artifacts-s3-01"
        mock_env_vars["DISABLE_AUTO_UPLOAD"] = "false"
        env_patcher = unittest.mock.patch.dict(os.environ, mock_env_vars)
        env_patcher.start()
        a = JobRunner(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-vector-spec.yml"},
            "./tests/runners/dummy-vector-spec.yml",
            None,
        )
        a.start(args=[vector_file, vector_string])

        result_output_dir = os.path.join(
            self.testing_working_dir,
            "wfk123",
            "job123",
            "task123",
            "inputs",
            "vector_file",
        )

        remote_vector_path = os.path.join(
            self.testing_working_dir,
            "wfk123",
            "job123",
            "task123",
            "inputs",
            "vector_file",
            "test_abc.geojson",
        )

        with open(os.path.join(result_output_dir, "spec.json"), "r") as f:
            d = json.load(f)
        assert d["value"] == remote_vector_path

    async def test_handle_input_assets(self) -> None:
        class M(ModelWrapper):
            def __init__(self, config: str, protocol: str = "abfs", logger: Logger = None) -> None:
                super().__init__(config, protocol, logger)

            def setup(self):
                pass

            async def preprocess(self, vector_string: types.Vector, vector_file: types.Vector) -> Any:
                print(vector_file, vector_string)
                return {"vector_file": vector_file, "vector_string": vector_string}

            async def inference(self, vector_file, vector_string):
                return {"vector_file": vector_file, "vector_string": vector_string}

            async def postprocess(self, vector_file, vector_string) -> Any:
                s = types.String(name="string", value="hello world")
                return {
                    "string": s,
                }

        # creating a vector dummy input
        vector_file = {
            "format": "vector",
            "type": "url",
            "name": "vector_file",
            "value": "s3://d-platform-orchestrator-lulc-artifacts-s3-01/test_abc.geojson",
        }

        # creating a dummy string input
        vector_string = {
            "format": "vector",
            "type": "url",
            "name": "vector_string",
            "value": '{"type":"Feature","geometry":{"type":"Point","coordinates":[125.6,10.1]},"properties":{"name":"Dinagat Islands"}}',
        }

        mock_env_vars = copy.deepcopy(self.mock_env_vars)
        mock_env_vars["AUTO_DOWNLOAD_ASSETS"] = "true"
        mock_env_vars["REMOTE_PREFIX"] = "s3://d-platform-orchestrator-lulc-artifacts-s3-01"
        mock_env_vars["DISABLE_AUTO_UPLOAD"] = "false"
        env_patcher = unittest.mock.patch.dict(os.environ, mock_env_vars)
        env_patcher.start()
        a = JobRunner(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-vector-spec.yml"},
            "./tests/runners/dummy-vector-spec.yml",
            None,
        )
        a.start(args=[vector_file, vector_string])
        passed_vals = a.get_passed_inputs_dict()

        result_output_dir = os.path.join(
            self.testing_working_dir,
            "wfk123",
            "job123",
            "task123",
            "outputs",
            "string",
        )
        assert os.path.samefile(
            passed_vals["vector_file"]["value"],
            os.path.join(
                self.testing_working_dir,
                "wfk123",
                "job123",
                "task123",
                "inputs",
                "vector_file",
                "test_abc.geojson",
            ),
        )
        assert os.path.exists(os.path.join(str(result_output_dir), "spec.json"))
        with open(os.path.join(str(result_output_dir), "spec.json"), "r") as f:
            json.load(f)
        env_patcher.stop()
