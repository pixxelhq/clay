import asyncio
import logging
import os
import threading
import time
from abc import abstractmethod
from copy import deepcopy
from enum import Enum
from functools import cached_property
from pprint import pformat
from typing import Any, Dict, List, Optional, Union

import requests
import uvloop
from matter import fs
from matter.fs import AzureClient
from requests.adapters import HTTPAdapter, Retry

from clay.exceptions import FailedExecutionException
from clay.logger import ClayLogger, Logger, get_streamvalues, get_user_logs
from clay.utils import (
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
            logger = ClayLogger(
                self.__class__.__name__,
                False,
                create_buffer_handler=True,
                create_console_handler=True,
                create_user_logs_handler=True,
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
        output_containers = deepcopy(self.config.outputs)
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

    def __del__(self) -> None:
        self.cleanup_session()

    def cleanup_session(self) -> None:
        pass

    async def cleanup_inference(self) -> None:
        pass

    async def preprocess(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def inference(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def postprocess(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def infer(self, inputs: list) -> Dict[str, Any]:
        parsed_inputs = self._parse_inputs(inputs)
        try:
            _return_vals = await self.preprocess(**parsed_inputs)
            _return_vals = to_tuple_if_required(_return_vals)
            _return_vals = await self.inference(*_return_vals)
            _return_vals = to_tuple_if_required(_return_vals)
            if _return_vals is not None:
                _return_vals = await self.postprocess(*_return_vals)
                _return_vals = to_tuple_if_required(_return_vals)
                _return_vals = self.format_output(_return_vals)
            return _return_vals
        finally:
            await self.cleanup_inference()

    def get_logs(self) -> Optional[str]:
        """Returns all model logs stored in the buffered stream

        :return: model logs
        """
        return get_streamvalues(self.logger)

    def get_user_logs(self) -> Optional[str]:
        """Gets the user logs logged at INFO level or above with the model's logger

        :return: user logs
        """
        return get_user_logs(self.logger)


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
            logger = (
                ClayLogger(
                    f"{self._run_mode}_model_runner",
                    propagate=True,
                )
                .add_console_handler(level=logging.INFO)
                .add_buffer_handler(level=logging.DEBUG)
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
        self._logger.info("Initializing model...")
        self._model: ModelWrapper = self._modelcls(**self._model_args)
        self._logger.info("Model initialization complete.")

    def _run_event_loop(self, _loop: asyncio.AbstractEventLoop) -> None:
        self._logger.debug("Start model inference event loop ...")
        asyncio.set_event_loop(_loop)
        _loop.run_forever()
        self._logger.debug("Event loop stopped")

    def _init_model_inference_event_loop(self) -> None:
        self._logger.debug("Starting model inference thread ...")
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
        self._logger.debug("Started model inference thread.")

    def run_model_inference(
        self, inference_parameters: List[Dict[Any, Any]], *args: Any, **kwargs: Any
    ) -> Any:
        # find task_id and remove from inputs
        task_id = ""
        for i, item in enumerate(inference_parameters):
            if item["name"] == "task_id":
                task_id = item["value"]
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
        except Exception as exc:
            self._model.logger.error(exc, exc_info=exc)
            res["result"] = exc  # type: ignore[assignment]

        res["logs"] = self._model.get_logs()
        res["user_logs"] = self._model.get_user_logs()

        return res

    def _fire_callback(
        self,
        state: ModelStates = ModelStates.INPROGRESS,
        id: str = "",
        result: Dict[str, Any] = {},
        logs: str = "",
        user_logs: str = "",
        err_msg: str = "",
    ) -> bool:
        if self._dexter_clb_url is None or self._dexter_clb_url == "":
            self._logger.warning(
                "`ORCHESTRATOR_URL` not set, and hence not firing callback"
            )
            return False

        # Setting the headers
        headers = {}
        token = os.getenv("DEXTER_CLB_AUTH_TOKEN")
        if isinstance(token, str):
            authHeader = "Bearer " + token
        else:
            self._logger.warning(
                "`DEXTER_CLB_AUTH_TOKEN not set. This model will not be able to "
                + "communicate with the Orchestrator service and callbacks will be fired."
            )
            return False

        headers["Authorization"] = authHeader
        headers["Content-type"] = "application/json"

        # Responsible for firing the callback to orchestrator callback url.
        data = {
            "data": {
                "state": state.value,
                "id": id,
                "result": result,
                "logs": logs,
                "user_logs": user_logs,
                "err_msg": err_msg,
            }
        }
        self._logger.debug(f"Data for callback: {data}")

        session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
        )
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        resp = session.post(
            url=self._dexter_clb_url,
            json=data,
            headers=headers,
        ).json()
        self._logger.info(f"Response from orchestrator: {pformat(resp)}")
        if resp["successful_update"]:
            self._logger.info("Successfully updated state with Orchestrator.")
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
        # Accepts a clay.exceptions.SuccessfulExecutionException
        pass

    @abstractmethod
    def failure(
        self,
        exc: Union[Exception, FailedExecutionException],
        data: Dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        # Accepts a clay.exceptions.FailedExecutionException
        pass

    @abstractmethod
    def start(self, *args: Any, **kwargs: Any) -> None:
        pass
