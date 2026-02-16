import asyncio
import logging
import os
from abc import abstractmethod
from collections import defaultdict
from copy import deepcopy
from functools import cached_property
from logging import Logger
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import datatypes
from clay import type_utils, types
from clay.exceptions import FailedExecutionException
from clay.logger import ClayLogger, get_streamvalues
from clay.utils import (
    PRIMITIVE_TYPES,
    cast_inputs,
    get_current_utc_time_iso,
    yaml_to_namespace,
)

# Legacy FeatureFlags class removed - proto types are now the default

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
        self._outputs_buffer: List[datatypes.Data] = []
        self._opts = opts
        self._model_inf_start_time: str = ""
        self._model_inf_end_time: str = ""

    def output(self, val: datatypes.Data) -> None:
        self._outputs_buffer.append(val)

    def get_output_buffer(self) -> List[datatypes.Data]:
        return self._outputs_buffer

    def set_model_inf_start_time(self) -> None:
        self._model_inf_start_time = get_current_utc_time_iso()

    def set_model_inf_end_time(self) -> None:
        self._model_inf_end_time = get_current_utc_time_iso()

    def get_model_inf_times(self) -> types.ModelInfTimes:
        return types.ModelInfTimes(InfStartTime=self._model_inf_start_time, InfEndTime=self._model_inf_end_time)

class ModelWrapper:
    """The base class that wraps all user defined models. Every user defined model is expected
    to inherit this class. This enforces a defined structure on the user and ensures proper
    integration with execution modes.
    """

    __OVERRIDABLE_FUNCS__: List[str] = ["preprocess", "inference", "postprocess"]

    def __init__(
        self,
        config: str,
        logger: Optional[Logger] = None,
        enable_debug_logs: Optional[bool] = None,
    ) -> None:
        """
        Args:
            config (str): Path to model specification file.
            logger (Optional[Logger], optional):
                Custom logger. If not provided, _clay_ uses it's internal default logger.
                Defaults to None.
        """
        self.config = yaml_to_namespace(config)
        self.enable_debug_logs = enable_debug_logs
        if logger is None:
            log_level = logging.DEBUG if self.enable_debug_logs else logging.INFO
            logger = ClayLogger(logger_name=self.__class__.__name__, propagate=True, level=log_level)
        self.logger: Logger = logger
        self._inputs_prop_map: Dict[str, Any] = defaultdict(None)
        self._runner_properties: Dict[types._CommonEnvvars, Any] = defaultdict(None)

        self.run_setup()

    def run_setup(self) -> None:
        """Runs setup"""
        env_variables = getattr(self.config, "env", None)
        if env_variables is not None:
            env_dict = vars(env_variables)
            for key, value in env_dict.items():
                if key not in os.environ:
                    self.logger.debug(f"Setting environment variable {key} from config")
                    os.environ[key] = str(value)

        self.params = {}
        parameters = getattr(self.config, "parameters", None)
        if parameters is not None:
            parameters = filter(lambda x: len(x) > 0, parameters)
            for param in parameters:
                self.params[param["name"]] = cast_inputs(param["default"], param["type"].lower())
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
            if isinstance(item.get("value", None), str) and PRIMITIVE_TYPES[item["type"].lower()] is not str:
                item["value"] = cast_inputs(item["value"], item["type"])

        # filling in default values for any missing inputs
        provided_inputs = [item.get("name", None) for item in inputs]
        for param in self.config.inputs:
            if param["name"] not in provided_inputs:
                _param = {**param}
                _param["value"] = cast_inputs(_param.pop("default"), _param["type"].lower())
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

    @abstractmethod
    def get_progress(self) -> float:
        """Returns the current progress of the model.

        Returns:
            float: Current model progress.
        """
        pass

    @abstractmethod
    def set_progress(self, progress: float) -> None:
        """This method is an **absolute setter method**. Meaning, the current progress of the model would be set to
        _progress_ (assuming _progress_ is a valid value). The idea behind this method is to indicate *in absolute terms,
        what the is progress of a model at a particular point*. Unline, _add_progress_, this is not an additive method.

        Args:
            progress (float): The value to which current model progress is to be set
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def add_asset(self, file_path: str, io_name: str, is_input: bool = True):
        """This method allows user to add an input or output `asset` explicitly

        Args:
            file_path (str): path of asset to be added
            io_name (str): name of the input or output
            is_input (bool): set to false if asset is an output

        """
        pass

    @abstractmethod
    def set_disclaimer(self, disclaimerMsg: str) -> None:
        pass

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

    async def postprocess(self, *args: Any, **kwargs: Any) -> Dict[str, datatypes.Data]:
        """The postprocess abstract method. This is the third method that the user is **compulsorily**
        required to defined.

        The arguments to this method are to be defined by the user.

        !!! warning
            The arguments should be same as the keys of the dictionary returned from
            the inference method.

        Raises:
            NotImplementedError: Raised during runtime if the method is not defined.

        Returns:
            Dict[str, datatypes.Data]: Returns a dict of values.
        """
        raise NotImplementedError

    async def infer(self, inputs: Dict[str, Any], opts: Optional[types.InferenceOpts]) -> InferenceCtx:
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

        d: Dict[str, Union[datatypes.DataWrapper, datatypes.Data]] = inputs
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
            assert isinstance(v, datatypes.Data), f"return value can only be of {datatypes.Data}"
            _inf_ctx.output(v)

        return _inf_ctx

    def get_logs(self) -> Optional[str]:
        """returns the logger buffer as a string"""
        return get_streamvalues(self.logger)


ModelWrapperType = TypeVar("ModelWrapperType", bound=ModelWrapper)


class BaseRunner(object):
    """The base class that wraps all runner implementations."""

    def __init__(
        self,
        modelcls: Type[ModelWrapper],
        model_args: Dict[str, Any],
        cfg_path: str,
        logger: Union[None, Logger],
        enable_debug_logs: Optional[bool] = None,
    ) -> None:
        self._modelcls = modelcls
        self._model_args = model_args
        self.config = yaml_to_namespace(cfg_path)
        self.enable_debug_logs = enable_debug_logs
        if logger is None:
            log_level = logging.DEBUG if self.enable_debug_logs else logging.INFO
            logger = ClayLogger(
                logger_name="model_runner",
                propagate=True,
                level=log_level,
            )
        assert isinstance(logger, Logger)
        self._logger: Logger = logger

        # Legacy feature flags removed - proto types are now the default

    def __init_subclass__(cls) -> None:
        assert "_collect_inputs" in dir(cls)
        assert "failure" in dir(cls) 

    @property
    def logger(self) -> Logger:
        return self._logger

    # Legacy set_feature_flag_on method removed - proto types are now the default

    # Legacy is_feature_flag_on method removed - proto types are now the default

    # Legacy __set_feature_flags__ method removed - proto types are now the default

    def _init_model(self) -> None:
        self.logger.info("Initializing Model...")
        self._model: ModelWrapper = self._modelcls(**self._model_args)
        self.logger.info("Model initialization complete.")

    @abstractmethod
    def _collect_inputs(
        self, inputs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[
        Union[
            Dict[str, Any],
            Tuple[Dict[str, datatypes.DataWrapper], Dict[str, Any]],
        ]
    ]:
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
    def _flush_output_buffer(self, output_buffer: List[datatypes.DataWrapper]) -> None:
        pass

    @abstractmethod
    def start(self, **kwargs: Any) -> None:
        pass
