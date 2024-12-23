# type: ignore

import os
import pathlib
import shutil
import unittest
from typing import Any, Optional
from unittest import mock

import datatypes
import shortuuid

from clay import ModelWrapper, types
from clay.core import FeatureFlags
from clay.logger import Logger
from clay.runners.job_runner import JobRunner
from clay.runners.job_runner_v2 import JobRunnerV2, _ArgoConfEnvVars, _InjectedEnvVars


class TestJobRunner_ProgessUpdates(unittest.IsolatedAsyncioTestCase):
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
            "TASK_ID": "task123",
            "JOB_ID": "job123",
            "WORKFLOW_ID": "wfk123",
            "LOCAL_WORKING_DIR": self.testing_working_dir,
            "working-dir": self.testing_working_dir,
            "inputs-working-dir": input_working_dir,
            "outputs-working-dir": output_working_dir,
            "outputs-remote-path": "s3://workflow-id/job-id/task-id/outputs/",
            "env": "local",
            "AWS_PROFILE": "d-platform-services",
            "ORCHESTRATOR_URL": "localhost",
            FeatureFlags.ForceInputTypesToV2.value: "1",
            FeatureFlags.ForceOutputTypesToV2.value: "1",
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.testing_working_dir)

    @mock.patch("clay._network.requests.Session.post")
    async def test_e2e_progress_update_sequence(self, mock_post) -> None:
        mock_response = mock.Mock()
        mock_response.json.return_value = {"data": {"successful_update": "True", "updated_fields": {}, "err": ""}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        class M(ModelWrapper):
            def __init__(
                _self,
                config: str,
                protocol: str = "abfs",
                logger: Optional[Logger] = None,
                enable_debug_logs: Optional[bool] = None,
            ) -> None:
                super().__init__(config, protocol, logger, enable_debug_logs)

            def setup(_self):
                pass

            async def preprocess(_self, string, raster) -> Any:
                _self.set_progress(25)
                return {"raster": raster, "string": string}

            async def inference(_self, raster, string) -> None:
                dummy_raster = pathlib.Path("../clipped.tiff")
                dummy_raster.touch()
                _self.add_progress(15)
                return {"raster": str(dummy_raster), "string": "this is hello"}

            async def postprocess(_self, raster, string) -> Any:
                _self.add_progress(25)
                _self.set_progress(87.4)
                r = datatypes.Raster(
                    format=datatypes.Format.raster,
                    type="url",
                    name="result",
                    value=raster,
                )
                s = types.String(format=datatypes.Format.string, type="str", name="string", value=string)
                return {
                    "result": r,
                    "string": s,
                }

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
        env_patcher.stop()

        call_args = mock_post.call_args_list
        assert call_args[0][1]["json"]["data"]["progress"] == 5.0
        assert call_args[1][1]["json"]["data"]["progress"] == 25.0
        assert call_args[2][1]["json"]["data"]["progress"] == 40.0
        assert call_args[3][1]["json"]["data"]["progress"] == 65.0
        assert call_args[4][1]["json"]["data"]["progress"] == 87.4
        assert call_args[5][1]["json"]["data"]["progress"] == 100.0


class TestJobRunnerV2_ProgessUpdates(unittest.IsolatedAsyncioTestCase):
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
            _InjectedEnvVars.TaskId.value: "task123",
            _InjectedEnvVars.WorkingDir.value: self.testing_working_dir,
            _InjectedEnvVars.InputsWorkingDir.value: input_working_dir,
            _InjectedEnvVars.OutputsWorkingDir.value: output_working_dir,
            _InjectedEnvVars.OutputsRemotePath.value: "",
            _ArgoConfEnvVars.ArgoTemplate.value: '{"inputs": {"parameters":[{"name": "string", "value":"hello world"}]}}',  # noqa
            _InjectedEnvVars.Env.value: "local",
            "ORCHESTRATOR_URL": "123",
            FeatureFlags.ForceInputTypesToV2.value: "1",
            FeatureFlags.ForceOutputTypesToV2.value: "1",
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.testing_working_dir)

    @mock.patch("clay._network.requests.Session.post")
    async def test_e2e_progress_update_sequence(self, mock_post) -> None:
        mock_response = mock.Mock()
        mock_response.json.return_value = {"data": {"successful_update": "True", "updated_fields": {}, "err": ""}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        class M(ModelWrapper):
            def __init__(
                _self,
                config: str,
                protocol: str = "abfs",
                logger: Optional[Logger] = None,
                enable_debug_logs: Optional[bool] = None,
            ) -> None:
                super().__init__(config, protocol, logger, enable_debug_logs)

            def setup(_self):
                pass

            async def preprocess(_self, string) -> Any:
                _self.set_progress(25)
                return {"string": string}

            async def inference(_self, string) -> None:
                _self.set_progress(43)
                return {"string": "this is hello"}

            async def postprocess(_self, string) -> Any:
                _self.add_progress(25)
                s = datatypes.String(format=datatypes.Format.string, type="url", name="string", value=string)
                return {
                    "string": s,
                }

        env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
        env_patcher.start()
        a = JobRunnerV2(
            "dummy",
            M,
            {"config": "./tests/runners/dummy-spec-2.yml"},
            "./tests/runners/dummy-spec-2.yml",
            None,
        )
        a.start()
        env_patcher.stop()

        call_args = mock_post.call_args_list
        assert call_args[0][1]["json"]["data"]["progress"] == 5.0
        assert call_args[1][1]["json"]["data"]["progress"] == 25.0
        assert call_args[2][1]["json"]["data"]["progress"] == 43.0
        assert call_args[3][1]["json"]["data"]["progress"] == 68.0
        assert call_args[4][1]["json"]["data"]["progress"] == 100.0
