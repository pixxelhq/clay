import asyncio
import logging
import threading
import time
from abc import abstractmethod
from typing import Any, Dict, List, Union

import uvloop
from matter import fs

from ramen.config import get_config
from ramen.exceptions import FailedExecutionException, SuccessfulExecutionException
from ramen.logger import get_logger
from ramen.utils import Converters, to_tuple_if_required


class ModelWrapper:

    __OVERRIDABLE_FUNCS__: List[str] = ["preprocess", "inference", "postprocess"]

    def __init__(self, config: str, protocol: str = "abfs") -> None:
        self._fs = fs.filesystem(protocol=protocol)
        self.configs = get_config(config)
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

    async def infer(self, inputs: dict) -> Any:

        parsed_inputs = self._parse_inputs(inputs)
        _return_vals = await self.preprocess(**parsed_inputs)
        print(_return_vals)
        _return_vals = to_tuple_if_required(_return_vals)
        print(_return_vals)
        _return_vals = await self.inference(*_return_vals)
        print(_return_vals)
        _return_vals = to_tuple_if_required(_return_vals)
        print(_return_vals)
        if _return_vals is not None:
            _return_vals = await self.postprocess(*_return_vals)
        return _return_vals


class BaseRunner(object):

    _SUPPORTED_RUN_MODES: List[str] = ["rmq", "http", "job"]
    _DEFAULT_EVENT_LOOP_POLICY = uvloop.EventLoopPolicy()

    def __init__(
        self,
        run_mode: str,
        modelcls: ModelWrapper,
        model_args: Dict[str, Any],
        logger: Union[None, logging.Logger],
        enable_uvloop: bool = False,
    ) -> None:
        self.run_mode = run_mode
        self._modelcls = modelcls
        self._model_args = model_args
        self._enable_uvloop = enable_uvloop
        # self._loop: Union[None, asyncio.AbstractEventLoop] = None
        if logger is None:
            logger = get_logger(f"{self._run_mode}_model_runner")
        self.logger = logger

    @property
    def run_mode(self) -> str:
        return self._run_mode

    @run_mode.setter
    def run_mode(self, value: str) -> None:
        if value not in self._SUPPORTED_RUN_MODES:
            raise ValueError(f"Invalid Run mode: {value}")
        self._run_mode = value

    def _init_model(self) -> None:
        self.logger.info("Starting model initialization ...")
        self._model = self._modelcls(**self._model_args)
        self.logger.info("Model initialization complete.")

    def _run_event_loop(self, _loop: asyncio.AbstractEventLoop) -> None:
        self.logger.info("Start model inference event loop ...")
        asyncio.set_event_loop(_loop)
        _loop.run_forever()
        self.logger.info("Event loop stopped")

    def _init_model_inference_event_loop(self) -> None:

        self.logger.info("Starting model inference thread ...")
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
        self.logger.info("Started model inference thread.")

    def run_model_inference(self, inference_parameters: Dict[str, Any]) -> Any:
        try:
            res = asyncio.run_coroutine_threadsafe(
                self._model.infer(inference_parameters), self._loop
            )
            return res.result()
        except SuccessfulExecutionException as exc:
            self.success(exc)
        except FailedExecutionException as exc:
            self.failure(exc)

    @abstractmethod
    def success(self, exc: Union[Exception, SuccessfulExecutionException]) -> None:
        # Accepts a ramen.exceptions.SuccessfulExecutionException
        pass

    @abstractmethod
    def failure(self, exc: Union[Exception, FailedExecutionException]) -> None:
        # Accepts a ramen.exceptions.FailedExecutionException
        pass

    @abstractmethod
    def start(self, *args: Any, **kwargs: Any) -> None:
        pass
