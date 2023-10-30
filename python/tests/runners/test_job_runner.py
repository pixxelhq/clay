import copy
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
from clay.runners.job_runner import JobRunner


class TestJobRunner(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        # truncating is fine since this is anyway a tmp directory
        self.testing_working_dir = f"./tmp-{shortuuid.random()[:5]}"
        os.mkdir(self.testing_working_dir)
        input_working_dir = os.path.join(self.testing_working_dir, "inputs")
        output_working_dir = os.path.join(self.testing_working_dir, "outputs")
        os.mkdir(input_working_dir)
        # os.mkdir(output_working_dir)

        # creating dummy inputs
        self.mock_env_vars = {
            "task-id": "task123",
            "working-dir": self.testing_working_dir,
            "inputs-working-dir": input_working_dir,
            "outputs-working-dir": output_working_dir,
            "outputs-remote-path": "s3://workflow-id/job-id/task-id/outputs/",
            "env": "local",
            "AWS_PROFILE": "d-platform-services",
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
            "value": "s3://bucket/another-bucket/clipped.tiff",
        }

        # creating a dummy string input
        string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        task_id = {
            "format": "string",
            "name": "task-id",
            "type": "str",
            "value": "task123",
        }
        job_id = {
            "format": "string",
            "name": "job-id",
            "type": "str",
            "value": "job123",
        }
        workflow_id = {
            "format": "string",
            "name": "workflow-id",
            "type": "str",
            "value": "wfk123",
        }
        local_working_dir = {
            "format": "string",
            "name": "local-working-dir",
            "type": "str",
            "value": self.testing_working_dir,
        }
        env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        a = JobRunner(
            "dummy",
            M,
            {"config": "./python/tests/runners/dummy-spec.yml"},
            "./python/tests/runners/dummy-spec.yml",
            None,
        )
        a.start(args=[raster, string, task_id, job_id, workflow_id, local_working_dir])
        passed_vals = a.get_passed_inputs_dict()

        assert passed_vals["raster"]["value"] == raster["value"]
        assert passed_vals["string"]["value"] == "hello world"
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
            "value": "s3://bucket/another-bucket/clipped.tiff",
        }

        # creating a dummy string input
        string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        task_id = {
            "format": "string",
            "name": "task-id",
            "type": "str",
            "value": "task123",
        }
        job_id = {
            "format": "string",
            "name": "job-id",
            "type": "str",
            "value": "job123",
        }
        workflow_id = {
            "format": "string",
            "name": "workflow-id",
            "type": "str",
            "value": "wf123",
        }
        local_working_dir = {
            "format": "string",
            "name": "local-working-dir",
            "type": "str",
            "value": self.testing_working_dir,
        }
        env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        a = JobRunner(
            "dummy",
            M,
            {"config": "./python/tests/runners/dummy-spec.yml"},
            "./python/tests/runners/dummy-spec.yml",
            None,
        )
        a.start(args=[raster, string, task_id, job_id, workflow_id, local_working_dir])
        passed_vals = a.get_passed_inputs_dict()

        assert passed_vals["raster"]["value"] == raster["value"]
        assert passed_vals["string"]["value"] == "hello world"
        env_patcher.stop()

        target_raster_asset_path = os.path.join(
            self.testing_working_dir,
            workflow_id["value"],
            job_id["value"],
            task_id["value"],
            "outputs",
            "result",
            "clipped.tiff",
        )
        target_raster_spec_path = os.path.join(
            self.testing_working_dir,
            workflow_id["value"],
            job_id["value"],
            task_id["value"],
            "outputs",
            "result",
            "spec.json",
        )
        target_string_spec_path = os.path.join(
            self.testing_working_dir,
            workflow_id["value"],
            job_id["value"],
            task_id["value"],
            "outputs",
            "string",
            "spec.json",
        )

        assert os.path.exists(target_raster_asset_path)
        assert os.path.exists(target_raster_spec_path)
        assert os.path.exists(target_string_spec_path)

    async def test_read_inputs_and_download_remote_asset(self) -> None:
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
            "value": "s3://d-platform-orchestrator-lulc-artifacts-s3-01/test-raster.tiff",
        }

        # creating a dummy string input
        string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        task_id = {
            "format": "string",
            "name": "task-id",
            "type": "str",
            "value": "task123",
        }
        job_id = {
            "format": "string",
            "name": "job-id",
            "type": "str",
            "value": "job123",
        }
        workflow_id = {
            "format": "string",
            "name": "workflow-id",
            "type": "str",
            "value": "wfk123",
        }
        local_working_dir = {
            "format": "string",
            "name": "local-working-dir",
            "type": "str",
            "value": self.testing_working_dir,
        }
        mock_env_vars = copy.deepcopy(self.mock_env_vars)
        mock_env_vars["AUTO_DOWNLOAD_ASSETS"] = "true"
        mock_env_vars["REMOTE_PREFIX"] = "s3://d-platform-orchestrator-lulc-artifacts-s3-01"
        env_patcher = unittest.mock.patch.dict(os.environ, mock_env_vars)
        env_patcher.start()
        a = JobRunner(
            "dummy",
            M,
            {"config": "./python/tests/runners/dummy-spec.yml"},
            "./python/tests/runners/dummy-spec.yml",
            None,
        )
        a.start(args=[raster, string, task_id, job_id, workflow_id, local_working_dir])
        passed_vals = a.get_passed_inputs_dict()

        raster_input_dir = os.path.join(
            self.testing_working_dir,
            workflow_id["value"],
            job_id["value"],
            task_id["value"],
            "inputs",
            "raster",
        )

        assert os.path.samefile(
            passed_vals["raster"]["value"],
            os.path.join(
                self.testing_working_dir,
                workflow_id["value"],
                job_id["value"],
                task_id["value"],
                "inputs",
                "raster",
                "test-raster.tiff",
            ),
        )
        assert passed_vals["string"]["value"] == "hello world"
        assert os.path.exists(os.path.join(raster_input_dir, "test-raster.tiff"))
        with open(os.path.join(raster_input_dir, "spec.json"), "r") as f:
            d = json.load(f)
        assert os.path.samefile(
            d["value"], os.path.join(raster_input_dir, "test-raster.tiff")
        )
        env_patcher.stop()

    async def test_auto_upload_generated_assets_enabled_success(self) -> None:
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
            "value": "s3://d-platform-orchestrator-lulc-artifacts-s3-01/test-raster.tiff",
        }

        # creating a dummy string input
        string = {
            "format": "string",
            "name": "string",
            "type": "str",
            "value": "hello world",
        }

        task_id = {
            "format": "string",
            "name": "task-id",
            "type": "str",
            "value": "task123",
        }
        job_id = {
            "format": "string",
            "name": "job-id",
            "type": "str",
            "value": "job123",
        }
        workflow_id = {
            "format": "string",
            "name": "workflow-id",
            "type": "str",
            "value": "wfk123",
        }
        local_working_dir = {
            "format": "string",
            "name": "local-working-dir",
            "type": "str",
            "value": self.testing_working_dir,
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
            {"config": "./python/tests/runners/dummy-spec.yml"},
            "./python/tests/runners/dummy-spec.yml",
            None,
        )
        a.start(args=[raster, string, task_id, job_id, workflow_id, local_working_dir])
        passed_vals = a.get_passed_inputs_dict()

        result_output_dir = os.path.join(
            self.testing_working_dir,
            workflow_id["value"],
            job_id["value"],
            task_id["value"],
            "outputs",
            "result",
        )
        remote_raster_path = os.path.join(
            "s3://d-platform-orchestrator-lulc-artifacts-s3-01",
            workflow_id["value"],
            job_id["value"],
            task_id["value"],
            "outputs",
            "result",
            "clipped.tiff",
        )

        assert os.path.samefile(
            passed_vals["raster"]["value"],
            os.path.join(
                self.testing_working_dir,
                workflow_id["value"],
                job_id["value"],
                task_id["value"],
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
        env_patcher.stop()
