import asyncio
import os
import threading
import time
from abc import abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union, cast

import requests
import uvloop
from matter import fs  # type: ignore[import]

from .config import get_config
from .exceptions import FailedExecutionException
from .logger import Logger, RamenLogger, get_streamvalues
from .utils import Converters, to_tuple_if_required


class ModelStates(Enum):
    STARTED = "TaskStarted"
    INPROGRESS = "TaskInprogress"
    COMPLETED = "TaskCompleted"
    FAILED = "TaskFailed"


class ModelWrapper:
    __OVERRIDABLE_FUNCS__: List[str] = ["preprocess", "inference", "postprocess"]

    def __init__(
        self,
        config: str,
        protocol: str = "abfs",
        logger: Optional[Logger] = None,
    ) -> None:
        self._fs = fs.filesystem(protocol=protocol)
        self.configs = get_config(config)
        if logger is None:
            logger = RamenLogger(
                "model_wrapper",
                False,
                create_buffer_handler=True,
                create_console_handler=True,
            )
        self.logger: Logger = cast(Logger, logger)
        self.setup(**self.configs.model.init)

    def __init_subclass__(cls) -> None:
        """Ensures all functions defined in __OVERRIDABLE_FUNCS__ are coroutines
        even when they are overriden in subclasses
        """
        for of in cls.__OVERRIDABLE_FUNCS__:
            func = getattr(cls, of, None)
            assert asyncio.iscoroutinefunction(func), (
                f"{of} is not a coroutine. "
                "Method signatures should start with `async def` instead of `def`"
            )

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass

    def setup(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    def _parse_inputs(self, inputs: dict) -> dict:
        parsed_inputs = {}

        for k, v in inputs.items():
            orig_targ_type = self.configs.model.inputs[k]["type"]
            targ_types = orig_targ_type.replace(" ", "").split(",")
            _found_type = False
            for ttype in targ_types:
                try:
                    parsed_inputs[k] = getattr(Converters, f"type_{ttype}")(v)
                    _found_type = True
                    if _found_type:
                        break
                except TypeError:
                    pass
            else:
                if not _found_type:
                    raise ValueError(
                        f"`{k}` received {type(v)} arguments "
                        f"while it expects `{orig_targ_type}`"
                    )
        return parsed_inputs

    async def preprocess(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def inference(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def postprocess(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def infer(self, inputs: dict) -> Dict[str, Any]:
        task_id = inputs.get("task_id", "")
        inputs.pop("task_id", None)
        parsed_inputs = self._parse_inputs(inputs)
        _return_vals = await self.preprocess(**parsed_inputs)
        _return_vals = to_tuple_if_required(_return_vals)
        _return_vals = await self.inference(*_return_vals)
        _return_vals = to_tuple_if_required(_return_vals)
        if _return_vals is not None:
            _return_vals = await self.postprocess(*_return_vals)
        res = {
            "id": task_id,
            "result": _return_vals,
            "logs": get_streamvalues(self.logger),
        }
        return res

    async def get_logs(self) -> str:
        """This method is used to extract logs from the main thread using
        `asyncio.run_coroutine_threadsafe` since the model runs in a separate
        thread from the main thread.
        """
        return get_streamvalues(self.logger)


class BaseRunner(object):
    _SUPPORTED_RUN_MODES: List[str] = ["rmq", "http", "job"]
    _DEFAULT_EVENT_LOOP_POLICY = uvloop.EventLoopPolicy()

    def __init__(
        self,
        run_mode: str,
        modelcls: ModelWrapper,
        model_args: Dict[str, Any],
        logger: Union[None, Logger],
        enable_uvloop: bool = False,
    ) -> None:
        self.run_mode = run_mode
        self._modelcls = modelcls
        self._model_args = model_args
        self._enable_uvloop = enable_uvloop
        self._dexter_clb_url = os.getenv("ORCHESTRATOR_URL")
        # self._loop: Union[None, asyncio.AbstractEventLoop] = None
        if logger is None:
            logger = RamenLogger(
                f"{self._run_mode}_model_runner", True, create_console_handler=True
            )
        assert isinstance(logger, Logger)
        self._logger: Logger = logger

    @property
    def run_mode(self) -> str:
        return self._run_mode

    @run_mode.setter
    def run_mode(self, value: str) -> None:
        if value not in self._SUPPORTED_RUN_MODES:
            raise ValueError(f"Invalid Run mode: {value}")
        self._run_mode = value

    def _init_model(self) -> None:
        self._logger.info("Starting model initialization ...")
        self._model: ModelWrapper = self._modelcls(**self._model_args)
        self._logger.info("Model initialization complete.")

    def _run_event_loop(self, _loop: asyncio.AbstractEventLoop) -> None:
        self._logger.info("Start model inference event loop ...")
        asyncio.set_event_loop(_loop)
        _loop.run_forever()
        self._logger.info("Event loop stopped")

    def _init_model_inference_event_loop(self) -> None:
        self._logger.info("Starting model inference thread ...")
        asyncio.set_event_loop_policy(self._DEFAULT_EVENT_LOOP_POLICY)
        self._loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self._t = threading.Thread(
            name="model_runner_event_thread",
            target=self._run_event_loop,
            args=(self._loop,),
            daemon=True,
        )
        self._t.start()
        time.sleep(1)
        self._logger.info("Started model inference thread.")

    def run_model_inference(
        self, inference_parameters: Dict[str, Any], *args: Any, **kwargs: Any
    ) -> Any:
        # fetching the task id for the current request
        task_id = inference_parameters.get("task_id", "")

        # setting the state of the current task state to `Inprogress`
        self._fire_callback(state=ModelStates.INPROGRESS, id=task_id)

        # Running the actual model inference
        try:
            res = asyncio.run_coroutine_threadsafe(
                self._model.infer(inference_parameters), self._loop
            ).result()
        except Exception as exc:
            if hasattr(exc, "logs") and exc.logs != "":
                logs = exc.logs
            else:
                logs = asyncio.run_coroutine_threadsafe(
                    self._model.get_logs(),
                    self._loop,
                ).result()
            res = {"id": task_id, "result": {}, "logs": logs}
            return self.failure(exc, data=res)

        return self.success(res)

    def _fire_callback(
        self,
        state: ModelStates = ModelStates.INPROGRESS,
        id: str = "",
        result: Dict[str, Any] = {},
        logs: Any = "",
    ) -> bool:
        if self._dexter_clb_url is None or self._dexter_clb_url == "":
            self._logger.warning(
                "`ORCHESTRATOR_URL` not set, and hence not firing callback"
            )
            return False

        # Responsible for firing the callback to orchestrator callback url.
        data = {"state": state.value, "id": id, "result": result, "logs": logs}
        self._logger.info(f"Data for callback: {data}")
        resp = requests.post(
            url=self._dexter_clb_url,
            json=data,
            headers={"Content-type": "application/json"},
        ).json()

        if resp["successful_update"]:
            self._logger.info("Updated state successfully.")
        else:
            self._logger.error("State Update failed.")

        return resp["successful_update"]

    @abstractmethod
    def success(
        self,
        result: Any,
        # exc: SuccessfulExecutionException,
        # *args: Any,
        # **kwargs: Any,
    ) -> Any:
        # Accepts a ramen.exceptions.SuccessfulExecutionException
        pass

    @abstractmethod
    def failure(
        self,
        exc: Union[Exception, FailedExecutionException],
        data: Dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        # Accepts a ramen.exceptions.FailedExecutionException
        pass

    @abstractmethod
    def start(self, *args: Any, **kwargs: Any) -> None:
        pass
