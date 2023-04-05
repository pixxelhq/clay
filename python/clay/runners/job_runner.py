import json
import sys
import time
from logging import Logger
from typing import Any, Dict, Union

from clay.core import BaseRunner, ModelStates, ModelWrapper
from clay.exceptions import FailedExecutionException
from clay.logger import get_streamvalues


class JobRunner(BaseRunner):
    RUN_MODE: str = "job"

    def __init__(
        self,
        model_name: str,
        modelcls: ModelWrapper,
        model_args: Dict[str, Any],
        logger: Union[None, Logger] = None,
        enable_uvloop: bool = True,
    ) -> None:
        super().__init__(JobRunner.RUN_MODE, modelcls, model_args, logger, enable_uvloop)
        self.model_name = model_name

    def success(self, output: Dict[str, Any]) -> Any:
        if self._dexter_clb_url is None:
            self._logger.warning("`ORCHESTRATOR_URL` not set, hence not firing callback.")
        else:
            _ = self._fire_callback(
                ModelStates.COMPLETED,
                output["task_id"],
                output["result"],
                output["logs"],
            )
        self._logger.info("Successful completion.")
        sys.exit(0)

    def failure(
        self,
        exc: Union[Exception, FailedExecutionException],
        data: Dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if self._dexter_clb_url is None:
            self._logger.warning(
                "`ORCHESTRATOR_URL` is not set, hence not firing callback."
            )
        else:
            _ = self._fire_callback(
                state=ModelStates.FAILED,
                id=data["task_id"],
                logs=data["logs"],
            )
        self._logger.error(f"Failure: {exc}", exc_info=exc)
        sys.exit(1)

    def start(self, *args: Any, **kwargs: Any) -> None:
        model_args = json.loads(args[0][0])
        try:
            self._init_model()
            self._init_model_inference_event_loop()
        except Exception as exc:
            self._logger.error(exc)
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            time.sleep(2)
            self._logger.info(f"Event loop running status: {self._loop.is_running()}")
            self._logger.info(f"thread alive status: {self._t.is_alive()}")

            # Since every job run, is mapped to a particular `task_id`,
            # incase if the model/event loop  fail to initialize, we can always fail
            # the corressponding `task_id` and store the `runner logs` so far.
            failure_data = {
                "task_id": model_args.get("task_id", ""),
                "result": {},
                "logs": get_streamvalues(self._logger),
            }
            self.failure(exc, failure_data)
        self._logger.info(args)
        res = self.run_model_inference(model_args)
        self._logger.info(f"Result: {res}")
        if isinstance(res["result"], Exception):
            self.failure(res["result"], res)
        else:
            self.success(res)
