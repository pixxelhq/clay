import sys
from typing import Any

sys.path.append("./tests/testrepo")

import pytest

from ramen import ModelWrapper


def test_mw_missing_setup_override() -> None:
    class M(ModelWrapper):
        async def preprocess(self, *args: Any, **kwargs: Any) -> Any:
            pass

    with pytest.raises(NotImplementedError):
        M(config="tests/testrepo/config.yaml")


def test_mw_blocking_method_override() -> None:

    with pytest.raises(AssertionError):

        class M(ModelWrapper):
            def setup(self) -> None:
                pass

            def preprocess(self, *args: Any, **kwargs: Any) -> Any:
                pass


def test_mw_parse_inputs(toy_model) -> None:

    # sanity check - conversion of int to string
    parsed_input = toy_model._parse_inputs({"i": 12})
    assert isinstance(parsed_input["i"], str)

    # testing string to int conversion for inputs
    toy_model.configs.model.inputs["i"]["type"] = "int"
    parsed_input = toy_model._parse_inputs({"i": "12"})
    assert isinstance(parsed_input["i"], int)


def test_mw_model_init() -> None:
    from entry import M  # type: ignore

    M(config="tests/testrepo/config.yaml")


@pytest.mark.asyncio
async def test_mw_model_inference() -> None:
    from entry import M  # type: ignore

    toy_model = M("./tests/testrepo/config.yaml")
    toy_output = await toy_model.infer({"i": "1"})
    assert toy_output == "ba1"


@pytest.mark.asyncio
async def test_mw_preprocess_returns_non_iterable() -> None:
    class M(ModelWrapper):
        def setup(self, a: str, x: list):
            pass

        async def preprocess(self, i: str) -> Any:
            return 1

        async def inference(self, i: str) -> Any:
            pass

        async def postprocess(self) -> Any:
            return None

    m = M("tests/testrepo/config.yaml")
    r = await m.infer({"i": "a"})
    assert r is None


@pytest.mark.asyncio
async def test_mw_preprocess_returns_multiple_values() -> None:
    class M(ModelWrapper):
        def setup(self, a: str, x: list):
            pass

        async def preprocess(self, i: str) -> Any:
            return 1, 2, {"a": 123}

        async def inference(self, a: int, b: int, c: dict) -> Any:
            return a, b, c

        async def postprocess(self, a: int, b: int, c: dict) -> Any:
            return a, b, c

    m = M("tests/testrepo/config.yaml")
    r = await m.infer({"i": 1})
    assert r == (1, 2, {"a": 123})


@pytest.mark.asyncio
async def test_mw_inference_returns_string() -> None:
    class M(ModelWrapper):
        def setup(self, a: str, x: list):
            pass

        async def preprocess(self, i: str) -> Any:
            return "abc"

        async def inference(self, a: str) -> Any:
            return "cba"

        async def postprocess(self, x: str) -> Any:
            return "123"

    m = M("tests/testrepo/config.yaml")
    r = await m.infer({"i": 1})
    assert r == "123"


@pytest.mark.asyncio
async def test_mw_inference_returns_none() -> None:
    class M(ModelWrapper):
        def setup(self, a: str, x: list):
            pass

        async def preprocess(self, i: str) -> Any:
            return 1, 2, {"a": 123}

        async def inference(self, a: int, b: int, c: dict) -> Any:
            return None

        async def postprocess(self) -> Any:
            pass

    m = M("tests/testrepo/config.yaml")
    r = await m.infer({"i": 1})
    assert r is None


@pytest.mark.asyncio
async def test_mw_missing_inference_override() -> None:
    class M(ModelWrapper):
        def setup(self, a: str, x: list):
            pass

        async def preprocess(self, i: str) -> Any:
            return 1, 2, {"a": 123}

        async def postprocess(self) -> Any:
            pass

    with pytest.raises(NotImplementedError):
        m = M("tests/testrepo/config.yaml")
        r = await m.infer({"i": 1})
        assert r is None
