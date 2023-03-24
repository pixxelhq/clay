import json
import unittest
from typing import Any, Dict
from unittest import mock

import pytest

import ramen
from ramen import ModelWrapper
from ramen.core import ModelStates
from ramen.runners import JobRunner


class M(ModelWrapper):
    def setup(self, a: str, x: list):
        pass

    async def preprocess(self, i: str) -> Any:
        self.logger.info("Some info in preprocess")
        if i == "f":
            self.logger.error("oops failed")
            ramen.failure("Failed")
        return 1, 2, {"a": 123}

    async def inference(self, a: int, b: int, c: Dict[str, int]) -> Any:
        return "c"

    async def postprocess(self, x: str) -> Any:
        self.logger.info("Some log")
        return "x"


class TestJobRunner(unittest.TestCase):
    def setUp(self) -> None:
        self._modelcls = M
        self._modelargs = {"config": "tests/testrepo/config.yaml"}

    def test_jobrunner_init(self) -> None:
        JobRunner(
            "demomodel",
            self._modelcls,
            self._modelargs,
        )

    @pytest.mark.skip(
        reason="no way of currently testing this until Orchestrator is up and running"
    )
    @mock.patch("ramen.core.requests.post")
    def test_jobrunner_success(self, mock_post: Any) -> None:
        mock_response = mock.Mock()
        mock_response.json.return_value = {"successful_update": "True", "err": ""}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        jr = JobRunner(
            "demomodel",
            self._modelcls,
            self._modelargs,
        )
        with pytest.raises(SystemExit) as exc:
            jr.start([json.dumps({"i": "a"})])

        call_args = mock_post.call_args_list

        # Asserting correct exit code
        assert exc.value.code == 0

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
    @mock.patch("ramen.core.requests.post")
    def test_jobrunner_failure(self, mock_post: Any) -> None:
        mock_response = mock.Mock()
        mock_response.json.return_value = {"successful_update": "True", "err": ""}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        jr = JobRunner(
            "demomodel",
            self._modelcls,
            self._modelargs,
        )
        with pytest.raises(SystemExit) as exc:
            jr.start([json.dumps({"i": "f"})])

        call_args = mock_post.call_args_list

        # Asserting correct exit code
        assert exc.value.code == 1

        # Here we assert that there should have been two state updates,
        # 1. State change to `TaskInprogress`
        # 2. State change to `TaskCompleted`
        # To verify this, we intercept the POST calls being made to the
        # `ORCHESTRATOR_URL` and check the json being sent there.
        assert call_args[0].kwargs["json"]["state"] == ModelStates.INPROGRESS.value
        assert call_args[0].kwargs["json"]["result"] == {}
        assert call_args[0].kwargs["json"]["logs"] == ""

        assert call_args[1].kwargs["json"]["state"] == ModelStates.FAILED.value
        assert call_args[1].kwargs["json"]["logs"] != ""
