import asyncio
import logging
import os
import threading
import time
from abc import abstractmethod
from collections import defaultdict
from copy import deepcopy
from enum import Enum
from functools import cached_property
from pprint import pformat
from typing import Any, Dict, List, Optional, Tuple, Union, get_args

import requests
import uvloop
from matter import fs
from matter.fs import AzureClient
from requests.adapters import HTTPAdapter, Retry

from clay import types
from clay.exceptions import FailedExecutionException
from clay.logger import ClayLogger, Logger, get_streamvalues, get_user_logs
from clay.utils import PRIMITIVE_TYPES, cast_inputs, yaml_to_namespace

DATA_SPEC_FILENAME: str = "spec.json"


class ValueTypes(Enum):
    STR = "str"
    URL = "url"
    INT = "int"
    FLOAT = "float"


class InferenceCtx:
    def __init__(self, opts: Optional[types.InferenceOpts] = None) -> None:
        self._outputs_buffer: types.OutputsBuffer = []
        self._opts = opts

    def output(self, val: types.Data) -> None:
        self._outputs_buffer.append(val)

    def get_output_buffer(self) -> types.OutputsBuffer:
        return self._outputs_buffer


class RunType(Enum):
    INFERENCE = "inference"
    WORKFLOW = "workflow"


model_inference_model_states_mapping = {
    types.ModelStates.INPROGRESS.value: types.InferenceStates.RUNNING.value,
    types.ModelStates.COMPLETED.value: types.InferenceStates.SUCCESS.value,
    types.ModelStates.FAILED.value: types.InferenceStates.FAILED.value,
}


model_inference_model_states_mapping = {
    types.ModelStates.INPROGRESS.value: types.InferenceStates.RUNNING.value,
    types.ModelStates.COMPLETED.value: types.InferenceStates.SUCCESS.value,
    types.ModelStates.FAILED.value: types.InferenceStates.FAILED.value,
}


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
        self._inputs_prop_map: Dict[str, Any] = defaultdict(None)

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

    @cached_property
    def receive_raw_inputs(self) -> bool:
        """returns the raw inputs accepted by the mode. If `False`, returns the inputs as
        processed by clay.

        Returns:
            bool: Returns processed inputs if value is set
        """
        return False

    def _dep_format_output(self, outputs: tuple) -> Any:
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

    def _dep_parse_inputs(self, inputs: list) -> dict:
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

    async def postprocess(self, *args: Any, **kwargs: Any) -> Dict[str, types.Data]:
        raise NotImplementedError

    async def infer(
        self, inputs: Dict[str, Any], opts: Optional[types.InferenceOpts]
    ) -> types.OutputsBuffer:
        _inf_ctx = InferenceCtx(opts=opts)
        try:
            _return_vals = await self.preprocess(**inputs)
            _return_vals = await self.inference(**_return_vals)
            _return_vals = await self.postprocess(**_return_vals)
        finally:
            await self.cleanup_inference()

        assert isinstance(_return_vals, dict), "postprocess can only return a dict"

        # TODO: evaluate returning a list of types vs returning a dict of types.
        # latter has duplication: `name` is both present in key and the type which is the
        # value
        for _, v in _return_vals.items():
            assert isinstance(
                v, get_args(types.Data)
            ), f"return value can only be one of {types.Data}"
            _inf_ctx.output(v)

        return _inf_ctx.get_output_buffer()

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
    _SUPPORTED_RUN_MODES: List[str] = ["argo", "http", "job"]
    _DEFAULT_EVENT_LOOP_POLICY = uvloop.EventLoopPolicy()

    def __init__(
        self,
        run_mode: str,
        modelcls: ModelWrapper,
        model_args: Dict[str, Any],
        cfg_path: str,
        logger: Union[None, Logger],
        enable_uvloop: bool = False,
    ) -> None:
        self.run_mode = run_mode
        self._modelcls = modelcls
        self._model_args = model_args
        self._enable_uvloop = enable_uvloop
        self._dexter_clb_url = os.getenv("ORCHESTRATOR_URL")
        self._dexter_host = os.getenv("DEXTER_HOST", "http://localhost")
        self._dexter_port = os.getenv("DEXTER_PORT", "8080")
        self.config = yaml_to_namespace(cfg_path)

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

    def __init_subclass__(cls) -> None:
        assert "output" in dir(cls)
        assert "_collect_inputs" in dir(cls)
        assert "failure" in dir(cls)

    @property
    def run_mode(self) -> str:
        return self._run_mode

    @run_mode.setter
    def run_mode(self, value: str) -> None:
        if value not in self._SUPPORTED_RUN_MODES:
            raise ValueError(f"Invalid Run mode: {value}")
        self._run_mode = value

    @property
    def logger(self) -> Logger:
        return self._logger

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

    def _fire_callback(self, clb: types.Callback) -> bool:
        if self._dexter_clb_url is None or self._dexter_clb_url == "":
            self._logger.warning(
                "`ORCHESTRATOR_URL` not set, and hence not firing callback"
            )
            return False

        # Setting the headers
        headers = {}
        resp = None
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
        session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
        )
        session.mount("http://", HTTPAdapter(max_retries=retries))

        run_type = os.getenv("DEXTER_RUN_TYPE", RunType.WORKFLOW.value)
        if run_type == RunType.WORKFLOW.value:
            if self._dexter_clb_url is None or self._dexter_clb_url == "":
                self._logger.warning(
                    "`ORCHESTRATOR_URL` not set, and hence not firing callback"
                )
                return False
            data = {"data": clb.model_dump(by_alias=True, exclude_none=True)}
            self._logger.debug(f"Data for callback: {data}")

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

        else:
            status = model_inference_model_states_mapping[clb.State.value]
            if status == "":
                self._logger.error(
                    f"State: {clb.State.value} is not supported by Orchestrator for inference"
                    + "Hence not firing callback"
                )
                return False
            data = {"status": status, "output": clb.Outputs}  # type: ignore
            self._logger.debug(f"Data for callback: {data}")

            resp = session.post(
                url="{0}:{1}/v1alpha1/inferences/{2}".format(
                    self._dexter_host, self._dexter_port, clb.Id
                ),
                json=data,
                headers=headers,
            )
            self._logger.info(f"Response from orchestrator: {pformat(resp)}")
            if resp.status_code == 204:
                self._logger.info("Successfully updated state with Orchestrator.")
            else:
                self._logger.error("State Update failed.")
            return True

    @abstractmethod
    def _collect_inputs(
        self, inputs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Union[Dict[str, Any], Tuple[Dict[str, types.Data], Dict[str, Any]]]]:
        pass

    @abstractmethod
    def output(
        self,
        key: str,
        value: Union[str, int, float],
        properties: Optional[
            Union[
                types.RasterProperties,
                types.VectorProperties,
                types.DateProperties,
                types.TabularProperties,
                Dict[str, Any],
            ]
        ] = None,
    ) -> None:
        pass

    @abstractmethod
    def run_model_inference(self, *args: Any, **kwargs: Any) -> Any:
        pass

    @abstractmethod
    def success(
        self,
        # exc: SuccessfulExecutionException,
        *args: Any,
        **kwargs: Any,
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
    def _flush_output_buffer(self, output_buffer: types.OutputsBuffer) -> None:
        pass

    @abstractmethod
    def start(self, *args: Any, **kwargs: Any) -> None:
        self.run_model_inference()
