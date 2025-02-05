import asyncio
import json
import logging
import os
import threading
import time
from abc import abstractmethod
from collections import defaultdict
from copy import deepcopy
from enum import Enum
from functools import cached_property
from logging import Logger
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import datatypes
import uvloop

from clay import _network, type_utils, types
from clay.exceptions import FailedExecutionException
from clay.logger import ClayLogger, get_streamvalues
from clay.utils import (
    PRIMITIVE_TYPES,
    cast_inputs,
    get_current_utc_time_iso,
    yaml_to_namespace,
)

DATA_SPEC_FILENAME: str = "spec.json"
CALLBACK_AUTH_METHOD_ENVVAR = "DEXTER_CALLBACK_AUTH"
SUB_HEADER_KEY: str = "X-AuthService-Sub"
ORGIDS_HEADER_KEY: str = "X-AuthService-Org_Ids"
SUB_ENVVAR: str = "DEXTER_GATEWAY_SUB"
ORGIDS_ENVVAR: str = "DEXTER_GATEWAY_ORGIDS"


class ValueTypes(Enum):
    STR = "str"
    URL = "url"
    INT = "int"
    FLOAT = "float"


class FeatureFlags(Enum):
    EnableTypesV2 = "FEATURE_ENABLE_TYPES_V2"
    ForceInputTypesToV2 = "FEATURE_FORCE_INPUT_TYPES_TO_V2"
    ForceOutputTypesToV2 = "FEATURE_FORCE_OUTPUT_TYPES_TO_V2"


C = TypeVar("C", bound="CallbackAuthMethod")


def running_locally() -> bool:
    """
    returns True if EXECUTOR_ENVVAR is not set, which means that we're running the model locally
    """
    return os.getenv(types.EXECUTOR_ENVVAR) is None


class CallbackAuthMethod(Enum):
    STATIC_TOKEN = 0
    JWT_TOKEN = 1
    GATEWAY_TOKEN = 2
    NO_AUTH = 3

    @classmethod
    def get_method(cls: Type[C]) -> C:
        val = os.getenv(CALLBACK_AUTH_METHOD_ENVVAR)
        if val is None:
            return cls(3)
        val = json.loads(val)
        return cls(val)


class InferenceCtx:
    """
    Utility object whose lifetime is scoped to a single inference run. This object is essentially used
    to move data in and out of a model wthin a runner. It also stores simple metrics recorded by the
    _ModelWrapper_ like inference start and end times among other things that are to be shipped
    back to orchestrator once the model execution completes.
    """

    def __init__(self, opts: Optional[types.InferenceOpts] = None) -> None:
        """
        Args:
            opts (Optional[types.InferenceOpts], optional):
                Data being passed into the model. Defaults to None.
        """
        self._outputs_buffer: types.OutputsBuffer = []
        self._opts = opts
        self._model_inf_start_time: str = ""
        self._model_inf_end_time: str = ""

    def output(self, val: types.Data) -> None:
        self._outputs_buffer.append(val)

    def get_output_buffer(self) -> types.OutputsBuffer:
        return self._outputs_buffer

    def set_model_inf_start_time(self) -> None:
        self._model_inf_start_time = get_current_utc_time_iso()

    def set_model_inf_end_time(self) -> None:
        self._model_inf_end_time = get_current_utc_time_iso()

    def get_model_inf_times(self) -> types.ModelInfTimes:
        return types.ModelInfTimes(
            InfStartTime=self._model_inf_start_time, InfEndTime=self._model_inf_end_time
        )


class RunType(Enum):
    INFERENCE = "inference"
    WORKFLOW = "workflow"


def callback_wrapper(conn_params: Dict[Any, str]):
    def _callback(
        logger: Logger, callback: types.Callback, enable_debug_logs: bool = False
    ) -> None:
        dexter_clb_url = conn_params.get(types._CommonEnvvars.ORCHESTRATOR_URL, None)

        task_id = conn_params.get(types._CommonEnvvars.TASK_ID, None)
        if not task_id:
            logger.warning("`task_id` not found hence aborting `mark_progress`")
            return None

        if callback.Id is None or callback.Id == "":
            callback.Id = task_id

        success = _network._fire_callback_to_dexter(
            callback, logger, dexter_clb_url, enable_debug_logs
        )
        if not success:
            logger.error("failed to fire callback")

    return _callback


class ModelWrapper:
    """The base class that wraps all user defined models. Every user defined model is expected
    to inherit this class. This enforces a defined structure on the user and ensures proper
    integration with execution modes.
    """

    __OVERRIDABLE_FUNCS__: List[str] = ["preprocess", "inference", "postprocess"]

    _DEFAULT_MODEL_PROGRESS_MIN: float = 0
    _DEFAULT_MODEL_PROGRESS_MAX: float = 100
    _DEFAULT_MODEL_USER_PROGRESS_MIN: float = 0
    _DEFAULT_MODEL_USER_PROGRESS_MAX: float = 95

    def __init__(
        self,
        config: str,
        protocol: str = "abfs",
        logger: Optional[Logger] = None,
        enable_debug_logs: Optional[bool] = None,
    ) -> None:
        """
        Args:
            config (str): Path to model specification file.
            protocol (str, optional):
                Storage protocol to be used internally. Defaults to "abfs".
            logger (Optional[Logger], optional):
                Custom logger. If not provided, _clay_ uses it's internal default logger.
                Defaults to None.
        """
        self.protocol = protocol
        self.config = yaml_to_namespace(config)
        if enable_debug_logs is None:
            self.enable_debug_logs = not self.is_running_locally
        else:
            self.enable_debug_logs = enable_debug_logs
        if logger is None:
            log_level = logging.DEBUG if self.enable_debug_logs else logging.INFO
            logger = ClayLogger(
                logger_name=self.__class__.__name__, propagate=True, level=log_level
            )
        self.logger: Logger = logger
        self._inputs_prop_map: Dict[str, Any] = defaultdict(None)

        self._runner_properties: Dict[types._CommonEnvvars, Any] = defaultdict(None)
        self._callback: Optional[Callable] = None
        self._progress_counter: float = 0.0

        self.run_setup()

    @property
    def is_running_locally(self) -> bool:
        return running_locally()

    def run_setup(self) -> None:
        """Runs setup"""
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
    def recieve_input_properties(self) -> bool:
        """
        Returns:
            bool: _description_
        """
        return False

    @cached_property
    def receive_raw_inputs(self) -> bool:
        """If set to `True`, `preprocess` would receive unprocessed, raw inputs,
        instead of data items cleaned and processed in to `clay.types`. This is
        generally a very unsafe operation and is not recommended. This kept for
        reasons for backward compatibility.
        """
        return False

    @cached_property
    def wrap_inputs(self) -> bool:
        return False

    def set_callback_callable(self, callback_fn: Callable) -> None:
        assert isinstance(callback_fn, Callable)
        self._callback = callback_fn

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
            assert asyncio.iscoroutinefunction(
                func
            ), f"{of} is not a coroutine. Method signatures should start with `async def` instead of `def`"

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass

    def setup(self, *args: Any, **kwargs: Any) -> None:
        """Abstract method that is to be overriden in the user model.
        This method will always run before any user code is executed. Any form of
        model setup code (download model weights etc) is to be defined in the `setup`
        method of the subclass (i.e. the model code).

        The arguments to this method are the items defined in the _parameter_ (WIP) section
        of the model spec file.
        """
        raise NotImplementedError

    def _dep_parse_inputs(self, inputs: list) -> dict:
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

    def get_progress(self) -> float:
        """Returns the current progress of the model.

        Returns:
            float: Current model progress.
        """
        return self._progress_counter

    def __check_progress_bounds(self, progress: float) -> bool:
        if progress < self._DEFAULT_MODEL_PROGRESS_MIN:
            self.logger.warning(
                "progress cannot be set to a value lower than min progress"
            )
            return False
        if progress > self._DEFAULT_MODEL_PROGRESS_MAX:
            self.logger.warning(
                "progress cannot be set to a value higher than the max progress"
            )
            return False
        return True

    def send_callback(self, callback: types.Callback) -> None:
        if callback.Progress is not None:
            if not self.__check_progress_bounds(callback.Progress):
                callback.Progress = None
            if callback.Progress and callback.Progress < self._progress_counter:
                self.logger.warning(
                    f"progress cannot be less than current progress, found: {callback.Progress}, current: {self._progress_counter}"
                )
                callback.Progress = None
            if callback.Progress:
                self._progress_counter = callback.Progress
        self._set_progress(callback, enable_debug_logs=True)

    def set_progress(self, progress: float) -> None:
        """This method is an **absolute setter method**. Meaning, the current progress of the model would be set to
        _progress_ (assuming _progress_ is a valid value). The idea behind this method is to indicate *in absolute terms,
        what the is progress of a model at a particular point*. Unline, _add_progress_, this is not an additive method.

        Args:
            progress (float): The value to which current model progress is to be set
        """
        if not self.__check_progress_bounds(progress):
            self.logger.warning(
                "progress cannot be set to a value higher than the max progress"
            )
            return None
        if progress < self._progress_counter:
            self.logger.warning(
                "progress cannot be set to a value lower than the current progress"
            )
            return None

        self._progress_counter = progress

        if self._callback is None:
            self.logger.warning("cannot fire callback as `_callback` is set to `None`")
            return None

        self._set_progress(
            types.Callback(
                Id="",
                State=types.ModelStates.INPROGRESS,
                Progress=self._progress_counter,
            )
        )
        return None

    def add_progress(self, progress_delta: float) -> None:
        """This method adds a progress `delta` to the progress calculated so far. The difference between
        `add_progress` and `set_progress` is that the `add_progress` is an **relative additive** method, while the
        `set_progress` is an *abosulte setter* method. `add_progress` *add* the *progress_delta* to the current progress.
        For example, if the progress of the model prior to the function call was 25 and _progress_delta_ was set to 5, post
        execution of this function the progress of the model would be 30.

        This method should be used when the model would want to indicate a certain delta in progress. For example, _every iteration
        of this loop would add a unit of 5 to the total model progress_.

        Args:
            progress_delta (float): Amount of change that is to be reflected in the model progress.

        """
        if progress_delta < self._DEFAULT_MODEL_USER_PROGRESS_MIN:
            self.logger.warning(
                "progress_delta cannot be set to a value lower than the min progress"
            )
            return None
        if progress_delta > self._DEFAULT_MODEL_USER_PROGRESS_MAX:
            self.logger.warning(
                "progress_delta cannot be set to a value higher than the max progress"
            )
            return None
        self._progress_counter += progress_delta
        self._set_progress(
            types.Callback(
                Id="",
                State=types.ModelStates.INPROGRESS,
                Progress=self._progress_counter,
            )
        )

    def _set_progress(
        self, callback: types.Callback, enable_debug_logs: bool = False
    ) -> None:
        if self._callback is None:
            self.logger.warning("cannot fire callback as `_callback` is set to `None`")
            return None

        if callback.Progress is None:
            callback.Progress = self._progress_counter

        self._callback(self.logger, callback, enable_debug_logs=enable_debug_logs)

    async def preprocess(self, *args: Any, **kwargs: Any) -> Any:
        """The preprocess abstract method. This the first method that the model
        needs to *compulsorily* override.

        The arguments are defined by the user and *has to* corressponds
        to the inputs mentioned in the *block spec* [WIP, link block spec inputs here].

        While there is no compulsion, the
        _recommended practice_ is that any type of data massaging and cleaning, like
        flattening, normalization etc, should be done here. Such that in the case of
        a runtime exception, it is easier to isolate the fault.

        This method can **only return a dict** wherein each key is a string identifier and
        the corressponding value could be of any type. The only contraint is that the next
        method in the chain (`inference` in this case) needs to have named arguments identical
        to the dictionary keys.

        !!! note
            There is a future plan to support tuples and lists as return values.

        Raises:
            NotImplementedError:
                Raised during runtime if the model doesn't implement the method.

        Returns:
            Any:
                Returns a Dict of values
        """
        raise NotImplementedError

    async def inference(self, *args: Any, **kwargs: Any) -> Any:
        """The inference abstact method. This is the second method that the user is **compulsorily**
        required to define.

        The arguments to this method are to be defined by the user.

        !!! warning
            The arguments should be same as the keys of the dictionary returned from
            the preprocess method.

        Raises:
            NotImplementedError: Raised during runtime if the method is not defined by the user.

        Returns:
            Any: Returns a Dict of values.
        """
        raise NotImplementedError

    async def postprocess(self, *args: Any, **kwargs: Any) -> Dict[str, types.Data]:
        """The postprocess abstract method. This is the third method that the user is **compulsorily**
        required to defined.

        The arguments to this method are to be defined by the user.

        !!! warning
            The arguments should be same as the keys of the dictionary returned from
            the inference method.

        Raises:
            NotImplementedError: Raised during runtime if the method is not defined.

        Returns:
            Dict[str, types.Data]: Returns a dict of values.
        """
        raise NotImplementedError

    async def infer(
        self, inputs: Dict[str, Any], opts: Optional[types.InferenceOpts]
    ) -> InferenceCtx:
        """Entrypoint to the model inference process. All runners would call the
        `infer` method defined on the model at a certain point to start the actual
        inference process.

        This is the common entrypoint into models used by all runner implementations.

        Internally, the `infer` method, would call the *three user defined* methods in
        the following order, **preprocess** -> **inference** -> **postprocess**

        Args:
            inputs (Dict[str, Any]):
                The inputs are provided to this method as a dictionary with string keys.
                If `receive_raw_inputs` is set to `True`, then the values would be python
                dictionaries. If set to `False`, the values would a type defined in
                `clay.types`.
            opts (Optional[types.InferenceOpts]):
                Data scoped to a single inference run. This contextual information
                is not used by the model in anyway. Rather this data is used by clay
                to perform housekeeping, infrastructur related tasks like callbacks
                and, more importantly, pass out a list of outputs to the runner.

                For more information, see [this faq.](faq.md#why-do-we-have-a-inferencectx-type-and-why-does-infer-return-a-inferencectx)

        Returns:
            InferenceCtx: A context class scoped to the inference run.
        """

        d: Dict[
            str, Union[datatypes.DataWrapperInterface, datatypes.Data, types.Data]
        ] = inputs
        if not self.wrap_inputs:
            # lift the wrapped types
            for key, value in inputs.items():
                d[key] = type_utils.lift_underlying_type(value)

        _inf_ctx = InferenceCtx(opts=opts)
        try:
            _inf_ctx.set_model_inf_start_time()
            _return_vals = await self.preprocess(**d)
            _return_vals = await self.inference(**_return_vals)
            _return_vals = await self.postprocess(**_return_vals)
            _inf_ctx.set_model_inf_end_time()
        finally:
            await self.cleanup_inference()

        assert isinstance(_return_vals, dict), "postprocess can only return a dict"

        # TODO: evaluate returning a list of types vs returning a dict of types.
        # latter has duplication: `name` is both present in key and the type which is the
        # value
        for _, v in _return_vals.items():
            assert isinstance(
                v, types.OutputBufferItem
            ), f"return value can only be of {types.OutputBufferItem}"
            _inf_ctx.output(v)

        return _inf_ctx

    def get_logs(self) -> Optional[str]:
        """returns the logger buffer as a string"""
        return get_streamvalues(self.logger)


ModelWrapperType = TypeVar("ModelWrapperType", bound=ModelWrapper)


class BaseRunner(object):
    """The base class that wraps all runner implementations."""

    _SUPPORTED_RUN_MODES: List[str] = ["argo", "http", "job"]
    _DEFAULT_EVENT_LOOP_POLICY = uvloop.EventLoopPolicy()

    def __init__(
        self,
        run_mode: str,
        modelcls: Type[ModelWrapper],
        model_args: Dict[str, Any],
        cfg_path: str,
        logger: Union[None, Logger],
        enable_uvloop: bool = False,
        enable_debug_logs: Optional[bool] = None,
    ) -> None:
        self.run_mode = run_mode
        self._modelcls = modelcls
        self._model_args = model_args
        self._enable_uvloop = enable_uvloop
        self._dexter_clb_url = os.getenv(types._CommonEnvvars.ORCHESTRATOR_URL.value, "")
        self._dexter_host = os.getenv(
            types._CommonEnvvars.DEXTER_HOST.value, "http://localhost"
        )
        self._dexter_port = os.getenv(types._CommonEnvvars.DEXTER_PORT.value, "8080")
        self.config = yaml_to_namespace(cfg_path)

        if enable_debug_logs is None:
            self.enable_debug_logs = not self.is_running_locally
        else:
            self.enable_debug_logs = enable_debug_logs
        # self._loop: Union[None, asyncio.AbstractEventLoop] = None
        if logger is None:
            log_level = logging.DEBUG if self.enable_debug_logs else logging.INFO
            logger = ClayLogger(
                logger_name=f"{self._run_mode}_model_runner",
                propagate=True,
                level=log_level,
            )
        assert isinstance(logger, Logger)
        self._logger: Logger = logger

        self._feature_flags = set()
        self.__set_feature_flags__()

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
    def is_running_locally(self) -> bool:
        return running_locally()

    @property
    def logger(self) -> Logger:
        return self._logger

    def set_feature_flag_on(self, *args: FeatureFlags) -> None:
        for ai in args:
            self._feature_flags.add(ai)

    def is_feature_flag_on(self, flag: FeatureFlags) -> bool:
        return flag.name in self._feature_flags

    def __set_feature_flags__(self):
        # env feature flags can only be set if the value of the env is 1
        # set is 1 and unset is 0
        for flag in FeatureFlags:
            env_value = os.getenv(flag.value)
            if env_value:
                try:
                    value = int(env_value)
                except:  # noqa: E722
                    self.logger.error(
                        f"invalid feature flag value received for {flag.name}: {env_value}"
                    )
                    continue
                if value == 1 and flag.name not in self._feature_flags:
                    self.logger.info(f"enabling {flag.name} via env")
                    self._feature_flags.add(flag.name)
                elif value == 0 and flag.name in self._feature_flags:
                    self.logger.info(f"disabling {flag.name} via env")
                    self._feature_flags.remove(flag.name)

    def _init_model(self) -> None:
        self.logger.info("Initializing Model...")
        self._model: ModelWrapper = self._modelcls(**self._model_args)
        self.logger.info("Model initialization complete.")

    def _run_event_loop(self, _loop: asyncio.AbstractEventLoop) -> None:
        self.logger.debug("Start model inference event loop ...")
        asyncio.set_event_loop(_loop)
        _loop.run_forever()
        self.logger.debug("Event loop stopped")

    def _init_model_inference_event_loop(self) -> None:
        self.logger.debug("Starting model inference thread ...")
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
        self.logger.debug("Started model inference thread.")

    @abstractmethod
    def _collect_inputs(
        self, inputs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[
        Union[
            Dict[str, Any],
            Tuple[Dict[str, datatypes.DataWrapperInterface], Dict[str, Any]],
        ]
    ]:
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
    def success(self) -> Any:
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
    def _flush_output_buffer(
        self, output_buffer: List[datatypes.DataWrapperInterface]
    ) -> None:
        pass

    @abstractmethod
    def start(self, **kwargs: Any) -> None:
        self.run_model_inference()

class EnvVarConfigItem:
    def __init__(self, name: str, required: bool = False, default: Any = None):
        self.name = name
        self.required = required
        self.default = default

    def get_value(self) -> Any:
        value = os.getenv(self.name, self.default)
        if self.required and value is None:
            raise ValueError(f"Required environment variable {self.name} is not set.")
        return value

class BaseConfigEnvVar:
    TaskId: EnvVarConfigItem = EnvVarConfigItem(name="TASK_ID", required=True, default=None)
    ClbUrl: EnvVarConfigItem = EnvVarConfigItem(name="ORCHESTRATOR_URL", required=True, default=None)
    
    def load_from_env(self):
        """Load environment variable values into instance attributes."""
        self.TaskId = self.TaskId.get_value()
        self.ClbUrl = self.ClbUrl.get_value()

def set_disclaimer(disclaimerMsg: str) -> None:
    config = BaseConfigEnvVar()
    config.load_from_env()
    logger = logging.getLogger(__name__)
    disclaimer_info = {'message': disclaimerMsg, 'timestamp': get_current_utc_time_iso()}
    callback = types.Callback(Id=str(config.TaskId), disclaimer=disclaimer_info)
    success = _network._fire_callback_to_dexter(callback, logger, str(config.ClbUrl), True)
    if not success:
        logger.error("failed to fire callback")
