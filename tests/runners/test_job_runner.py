import json
import unittest
from typing import Any, Dict

import pytest

import ramen
from ramen import ModelWrapper
from ramen.runners import JobRunner


class M(ModelWrapper):
    def setup(self, a: str, x: list):
        pass

    async def preprocess(self, i: str) -> Any:
        if i == "f":
            ramen.failure("Failed")
        return 1, 2, {"a": 123}

    async def inference(self, a: int, b: int, c: Dict[str, int]) -> Any:
        return "c"

    async def postprocess(self, x: str) -> Any:
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

    def test_jobrunner_success(self) -> None:
        jr = JobRunner(
            "demomodel",
            self._modelcls,
            self._modelargs,
        )
        with pytest.raises(SystemExit) as exc:
            jr.start([json.dumps({"i": "a"})])
        assert exc.value.code == 0

    def test_jobrunner_failure(self) -> None:
        jr = JobRunner(
            "demomodel",
            self._modelcls,
            self._modelargs,
        )
        with pytest.raises(SystemExit) as exc:
            jr.start([json.dumps({"i": "f"})])
        assert exc.value.code == 1
