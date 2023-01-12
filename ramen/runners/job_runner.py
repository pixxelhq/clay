import json
import logging
import sys
import time
from typing import Any, Dict, List, Union

from ramen.core import BaseRunner, ModelWrapper
from ramen.exceptions import FailedExecutionException, SuccessfulExecutionException


class JobRunner(BaseRunner):

    RUN_MODE: str = "job"

    def __init__(
        self,
        model_name: str,
        modelcls: ModelWrapper,
        model_args: Dict[str, Any],
        logger: Union[None, logging.Logger] = None,
        enable_uvloop: bool = True,
    ) -> None:
        super().__init__(JobRunner.RUN_MODE, modelcls, model_args, logger, enable_uvloop)
        self.model_name = model_name

    def success(
        self, exc: Union[Exception, SuccessfulExecutionException]
    ) -> None:
        self.logger.info(f"Success: {exc}")
        sys.exit(0)

    def failure(self, exc: Union[Exception, FailedExecutionException]) -> None:
        self.logger.error(f"Failure: {exc}")
        sys.exit(1)

    def start(self, args: List[str]) -> None:  # type: ignore
        try:
            self._init_model()
            self._init_model_inference_event_loop()
        except Exception as exc:
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            time.sleep(2)
            self.logger.info(f"Event loop running status: {self._loop.is_running()}")
            self.logger.info(f"thread alive status: {self._t.is_alive()}")
            self.failure(exc)
        self.logger.info(args)
        model_args = json.loads(args[0])
        res = self.run_model_inference(model_args)
        self.logger.info(f"Result: {res}")
        self.success(
            SuccessfulExecutionException("Model inference job completed successfully.")
        )
