"""
import json
import os
import sys
import time
import clay
from enum import Enum
from logging import Logger
from pprint import pformat
from typing import Any, Dict, Union, Tuple

from clay.core import BaseRunner, ModelStates, ModelWrapper
from clay.exceptions import FailedExecutionException
from clay.logger import get_streamvalues


class _InjectedEnvVars(Enum):
    WorkingDir = "working-dir"


class JobRunner(BaseRunner):
    RUN_MODE: str = "job"

    def __init__(
        self,
        model_name: str,
        modelcls: ModelWrapper,
        model_args: Dict[str, Any],
        cfg_path: str,
        logger: Union[None, Logger] = None,
        enable_uvloop: bool = True,
    ) -> None:
        super().__init__(
            JobRunner.RUN_MODE, modelcls, model_args, cfg_path, logger, enable_uvloop
        )
        self.model_name = model_name

    def get_injected_envvar(self, key: _InjectedEnvVars) -> Tuple[str, bool]:
        val = self._injected_envvars.get(key)
        if val is None:
            return "", False
        return val, True

    def set_injected_envvar(self, key: _InjectedEnvVars, val: str) -> None:
        self._injected_envvars[key] = val

    def read_injected_envvars(self) -> None:
        for e in _InjectedEnvVars:
            val = os.getenv(e.value)
            if val is None:
                self.logger.warn(f"env-var `{e.name}` not found")
                continue
            self.set_injected_envvar(e, val)

    def success(self, data: Dict[str, Any]) -> Any:
        if self._dexter_clb_url is None:
            self._logger.warning("`ORCHESTRATOR_URL` not set, hence not firing callback.")
        else:
            self._fire_callback(
                state=ModelStates.COMPLETED,
                id=data["task_id"],
                result=data["result"],
                logs=data.get("logs", ""),
                user_logs=data.get("user_logs", ""),
            )
        self._logger.info("Inferenece finished.")
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
            if isinstance(exc, FailedExecutionException):
                err_msg = exc.msg
            else:
                err_msg = ""
            self._fire_callback(
                state=ModelStates.FAILED,
                id=data["task_id"],
                logs=data.get("logs", ""),
                user_logs=data.get("user_logs", ""),
                err_msg=err_msg,
            )
        self._logger.error(f"Failure: {exc}", exc_info=exc)
        sys.exit(1)

    def start(self, inputs: Union[str, Dict[str, Any]]) -> None:
        if isinstance(inputs, str):
            model_args = json.loads(inputs)
        elif not isinstance(inputs, dict):
            raise TypeError(f"`inputs` type {type(inputs)} not supported")

        try:
            self._init_model()
            self._init_model_inference_event_loop()
        except Exception as exc:
            self._logger.error(exc)
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            time.sleep(2)
            self._logger.debug(f"Event loop running status: {self._loop.is_running()}")
            self._logger.debug(f"thread alive status: {self._t.is_alive()}")

            # Since every job run, is mapped to a particular `task_id`,
            # incase if the model/event loop  fail to initialize, we can always fail
            # the corressponding `task_id` and store the `runner logs` so far.
            failure_data = {
                "task_id": model_args.get("task_id", ""),
                "result": {},
                "logs": get_streamvalues(self._logger),
            }
            self.failure(exc, failure_data)
        self._logger.info(f"Model inputs:\n{pformat(args)}")
        res = self.run_model_inference(model_args)
        self._logger.info(f"Inference results:\n{pformat(res['result'])}")
        if isinstance(res["result"], Exception):
            self.failure(exc=res["result"], data=res)
        else:
            self.success(data=res)
"""
