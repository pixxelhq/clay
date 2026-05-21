import asyncio
import logging
import os
from abc import abstractmethod
from functools import cached_property
from logging import Logger
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

import datatypes

from clay.exceptions import FailedExecutionException
from clay.logger import ClayLogger
from clay.utils import (
    cast_inputs,
    yaml_to_namespace,
)


class InferenceCtx:
    """Utility object whose lifetime is scoped to a single inference run.

    Used to move data in and out of a block within a runner. Outputs produced
    by `postprocess` are buffered here for the runner to collect.
    """

    def __init__(self) -> None:
        self._outputs_buffer: List[datatypes.Data] = []

    def output(self, val: datatypes.Data) -> None:
        self._outputs_buffer.append(val)


class BlockWrapper:
    """The base class that wraps all user defined blocks. Every user defined block is expected
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
            config (str): Path to block specification file.
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
    def wrap_inputs(self) -> bool:
        return False

    def __init_subclass__(cls) -> None:
        """Ensures all functions defined in __OVERRIDABLE_FUNCS__ are coroutines
        even when they are overriden in subclasses
        """
        for of in cls.__OVERRIDABLE_FUNCS__:
            func = getattr(cls, of, None)
            assert asyncio.iscoroutinefunction(
                func
            ), f"{of} is not a coroutine. Method signatures should start with `async def` instead of `def`"

    def setup(self, *args: Any, **kwargs: Any) -> None:
        """Abstract method that is to be overriden in the user block.
        This method will always run before any user code is executed. Any form of
        block setup code (download block weights etc) is to be defined in the `setup`
        method of the subclass (i.e. the block code).

        The arguments to this method are the items defined in the _parameter_ (WIP) section
        of the block spec file.
        """
        raise NotImplementedError

    @abstractmethod
    def get_progress(self) -> float:
        """Returns the current progress of the block.

        Returns:
            float: Current block progress.
        """
        pass

    @abstractmethod
    def set_progress(self, progress: float) -> None:
        """This method is an **absolute setter method**. Meaning, the current progress of the block would be set to
        _progress_ (assuming _progress_ is a valid value). The idea behind this method is to indicate *in absolute terms,
        what the is progress of a block at a particular point*. Unline, _add_progress_, this is not an additive method.

        Args:
            progress (float): The value to which current block progress is to be set
        """
        pass

    @abstractmethod
    def add_progress(self, progress_delta: float) -> None:
        """This method adds a progress `delta` to the progress calculated so far. The difference between
        `add_progress` and `set_progress` is that the `add_progress` is an **relative additive** method, while the
        `set_progress` is an *abosulte setter* method. `add_progress` *add* the *progress_delta* to the current progress.
        For example, if the progress of the block prior to the function call was 25 and _progress_delta_ was set to 5, post
        execution of this function the progress of the block would be 30.

        This method should be used when the block would want to indicate a certain delta in progress. For example, _every iteration
        of this loop would add a unit of 5 to the total block progress_.

        Args:
            progress_delta (float): Amount of change that is to be reflected in the block progress.

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
        """The preprocess abstract method. This the first method that the block
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
                Raised during runtime if the block doesn't implement the method.

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

    def _validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Validate inputs against their specifications.

        Args:
            inputs: Dictionary of input name to DataWrapper

        Raises:
            datatypes.ValidationError: If validation fails
        """
        input_specs = {spec["name"]: spec for spec in self.config.inputs}

        for name, value in inputs.items():
            if name not in input_specs:
                continue
            spec = input_specs[name]
            if isinstance(value, datatypes.DataWrapper):
                datatypes.validate_input(value, spec)

    async def infer(self, inputs: Dict[str, Any]) -> InferenceCtx:
        """Entrypoint to the block inference process. All runners would call the
        `infer` method defined on the block at a certain point to start the actual
        inference process.

        This is the common entrypoint into blocks used by all runner implementations.

        Internally, the `infer` method, would call the *three user defined* methods in
        the following order, **preprocess** -> **inference** -> **postprocess**

        Args:
            inputs (Dict[str, Any]):
                The inputs are provided to this method as a dictionary with string keys.
                Values are typed items from the `datatypes` package.

        Returns:
            InferenceCtx: A context class scoped to the inference run.
        """
        self._validate_inputs(inputs)

        d: Dict[str, Union[datatypes.DataWrapper, datatypes.TypedDataView]] = inputs
        if not self.wrap_inputs:
            for key, value in inputs.items():
                if not isinstance(value, datatypes.DataWrapper):
                    raise TypeError("Only DataWrapper instances are supported")
                d[key] = value.typed_view()

        _inf_ctx = InferenceCtx()
        _return_vals = await self.preprocess(**d)
        _return_vals = await self.inference(**_return_vals)
        _return_vals = await self.postprocess(**_return_vals)

        assert isinstance(_return_vals, dict), "postprocess can only return a dict"

        # TODO: evaluate returning a list of types vs returning a dict of types.
        # latter has duplication: `name` is both present in key and the type which is the
        # value
        for _, v in _return_vals.items():
            assert isinstance(v, datatypes.Data), f"return value can only be of {datatypes.Data}"
            _inf_ctx.output(v)

        return _inf_ctx


class BaseRunner(object):
    """The base class that wraps all runner implementations."""

    def __init__(
        self,
        blockcls: Type[BlockWrapper],
        block_args: Dict[str, Any],
        cfg_path: str,
        logger: Union[None, Logger],
        enable_debug_logs: Optional[bool] = None,
    ) -> None:
        self._blockcls = blockcls
        self._block_args = block_args
        self.config = yaml_to_namespace(cfg_path)
        self.enable_debug_logs = enable_debug_logs
        if logger is None:
            log_level = logging.DEBUG if self.enable_debug_logs else logging.INFO
            logger = ClayLogger(
                logger_name="block_runner",
                propagate=True,
                level=log_level,
            )
        assert isinstance(logger, Logger)
        self._logger: Logger = logger

    def __init_subclass__(cls) -> None:
        assert "_collect_inputs" in dir(cls)
        assert "failure" in dir(cls)

    @property
    def logger(self) -> Logger:
        return self._logger

    def _init_block(self) -> None:
        self.logger.info("Initializing Block...")
        self._block: BlockWrapper = self._blockcls(**self._block_args)
        self.logger.info("Block initialization complete.")

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
    def start(self, **kwargs: Any) -> None:
        pass
