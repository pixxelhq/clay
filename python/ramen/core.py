import asyncio
import os
import threading
import time
from abc import abstractmethod
from copy import deepcopy
from enum import Enum
from functools import cached_property
from typing import Any, Dict, List, Optional, Union

import requests
import uvloop
from matter import fs
from matter.fs import AzureClient

from ramen.exceptions import FailedExecutionException
from ramen.logger import Logger, RamenLogger, get_streamvalues
from ramen.utils import (
    PRIMITIVE_TYPES,
    cast_inputs,
    to_tuple_if_required,
    yaml_to_namespace,
)


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
        self.protocol = protocol
        self.config = yaml_to_namespace(config)
        if logger is None:
            logger = RamenLogger(
                self.__class__.__name__,
                False,
                create_buffer_handler=True,
                create_console_handler=True,
            )
        self.logger: Logger = logger
        self.run_setup()

    def run_setup(self) -> None:
        self.params = {}
        parameters = getattr(self.config, "parameters", None)
        if parameters is not None:
            parameters = filter(lambda x: len(x) > 0, parameters)
            for param in parameters:
                self.params[param["name"]] = cast_inputs(
                    param["default"], param["type"].lower()
                )
        self.setup(**self.params)

    @cached_property
    def fs(self) -> AzureClient:
        filesystem = fs.filesystem(protocol=self.protocol)
        return filesystem

    @cached_property
    def recieve_input_properties(self) -> bool:
        return False

    def format_output(self, outputs: tuple) -> Any:
        output_containers = deepcopy(self.config.output)
        for output, output_container in zip(outputs, output_containers):
            output_container["value"] = output
            if not output_container.get("properties", False):
                output_container["properties"] = {}
        return output_containers

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

    def _parse_inputs(self, inputs: list) -> dict:
        """
        Makes sure all the inputs are correctly cast into expected types
        We leave items with unidentified `type`s as strings by default

        Returns a dict mapping the parameter names to one of:
            - the value of the parameter
            - the entire set of properties of the parameter along with the values
        """
        # remove empty dicts
        inputs = list(filter(lambda x: len(x) > 0, inputs))

        # We assume that json.loads has done most primitive type conversions and
        # only explicitly cast values that are still "incorrectly" left as strings.
        # Since this will almost never happen, the below step will likely
        # never actuall run, but is kept for safety
        # Casting Inputs:
        for item in inputs:
            if (
                isinstance(item.get("value", None), str)
                and PRIMITIVE_TYPES[item["type"].lower()] is not str
            ):
                item["value"] = cast_inputs(item["value"], item["type"])

        # filling in default values for any missing inputs
        provided_inputs = [item.get("name", None) for item in inputs]
        for param in self.config.inputs:
            if param["name"] not in provided_inputs:
                _param = {**param}
                _param["value"] = cast_inputs(
                    _param.pop("default"), _param["type"].lower()
                )
                inputs.append(_param)

        # Setting the key-value pairs as required
        if self.recieve_input_properties:
            result = {item["name"]: item for item in inputs}
        else:
            result = {item["name"]: item["value"] for item in inputs}

        return result

    async def preprocess(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def inference(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def postprocess(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def infer(self, inputs: list) -> Dict[str, Any]:
        parsed_inputs = self._parse_inputs(inputs)
        _return_vals = await self.preprocess(**parsed_inputs)
        _return_vals = to_tuple_if_required(_return_vals)
        _return_vals = await self.inference(*_return_vals)
        _return_vals = to_tuple_if_required(_return_vals)
        if _return_vals is not None:
            _return_vals = await self.postprocess(*_return_vals)
            _return_vals = to_tuple_if_required(_return_vals)
            _return_vals = self.format_output(_return_vals)
        return _return_vals

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
        self, inference_parameters: List[Dict[Any, Any]], *args: Any, **kwargs: Any
    ) -> Any:
        # find task_id and remove from inputs
        task_id = ""
        for i, item in enumerate(inference_parameters):
            if "task_id" in item.keys():
                task_id = item["task_id"]
                inference_parameters.pop(i)
                break

        # setting the state of the current task state to `Inprogress`
        self._fire_callback(state=ModelStates.INPROGRESS, id=task_id)

        # Running the actual model inference
        res = {"task_id": task_id, "result": {}, "logs": None}
        try:
            res["result"] = asyncio.run_coroutine_threadsafe(
                self._model.infer(inference_parameters), self._loop
            ).result()
            res["logs"] = asyncio.run_coroutine_threadsafe(
                self._model.get_logs(),
                self._loop,
            ).result()
        except Exception as exc:
            res["result"] = exc  # type: ignore[assignment]
            if hasattr(exc, "logs") and exc.logs != "":
                res["logs"] = exc.logs
            else:
                res["logs"] = ""
        return res

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
        data = {"data": {"state": state.value, "id": id, "result": result, "logs": logs}}
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
