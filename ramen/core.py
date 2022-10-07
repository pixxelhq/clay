import asyncio
from typing import Any, List

from matter import fs

from ramen.config import get_config
from ramen.utils import Converters, to_tuple_if_required


class ModelWrapper:

    __OVERRIDABLE_FUNCS__: List[str] = ["preprocess", "inference", "postprocess"]

    def __init__(self, config: str, protocol: str = "abfs") -> None:
        self._fs = fs.filesystem(protocol=protocol)
        self.configs = get_config(config)
        self.setup(self.configs.model.init)

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
                finally:
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
