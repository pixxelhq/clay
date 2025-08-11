import os
import time
import unittest
from typing import Any
import pytest
from clay import ModelWrapper
from clay.core import BaseRunner
from .models.ymxplusc import YMXPLUSC, YMXPLUSC_CONFIG

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
        class DemoRunner(BaseRunner):
            def __init__(self):
                super().__init__(
                    modelcls=YMXPLUSC,
                    model_args={"config": YMXPLUSC_CONFIG},
                    logger=None,
                    cfg_path=YMXPLUSC_CONFIG,
                )
                self._current_progress: float = 0.0
    
            def get_progress(self) -> float:
                return self._current_progress

            def set_progress(self, progress: float) -> None:
                if not (0 <= progress <= 100):
                    self._logger.error("Progress must be between 0 and 100.")
                    return None
                if progress < self._current_progress:
                    self.logger.warning("progress cannot be set to a value lower than the current progress")
                    return None
                self._current_progress = progress

            def add_progress(self, progress_delta: float) -> None:
                new_progress = self._current_progress + progress_delta
                self.set_progress(new_progress)

        self._test_modelcls = YMXPLUSC
        self._test_runnercls = DemoRunner
        time.sleep(1)

    def test_setup(self):
        os.environ["SAMPLE_ENV"] = "alreadyExists"
        self.r = self._test_runnercls()
        self.r._init_model()        
        assert os.environ["SAMPLE_ENV"] == "alreadyExists"
        assert os.environ["SAMPLE_ENV_1"] == "2"

    def test_model_init(self):
        self.r = self._test_runnercls()
        self.r._init_model()
        assert isinstance(self.r._model, self._test_modelcls)

    def test_progress_update(self):
        self.r = self._test_runnercls()
        self.r._init_model()

        self.r.set_progress(13)
        assert self.r.get_progress() == 13

        self.r.set_progress(26)
        assert self.r.get_progress() == 26

        self.r.add_progress(5)
        assert self.r.get_progress() == 31

        self.r.set_progress(100)
        assert self.r.get_progress() == 100

    def test_progress_update_with_multiple_increments_greater_than_max(self):
        self.r = self._test_runnercls()
        self.r._init_model()

        self.r.set_progress(100)
        assert self.r.get_progress() == 100

        self.r.set_progress(13)
        assert self.r.get_progress() == 100

    def test_progress_update_with_negative_increment(self):
        self.r = self._test_runnercls()
        self.r._init_model()

        assert self.r.get_progress() == 0
        self.r.set_progress(-10)
        assert self.r.get_progress() == 0