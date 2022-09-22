import asyncio
import multiprocessing
import sys

import aiohttp
import asynctest
import pytest

sys.path.append("tests/testrepo")
from entry import M  # type: ignore

from ramen.server import ServerWrapper, create_server

testrepo_config = "tests/testrepo/config.yaml"


@pytest.mark.asyncio
async def test_sw_init() -> None:
    ServerWrapper(model_cls=M, model_config=testrepo_config)


@pytest.mark.asyncio
async def test_sw_set_app_invalid_type() -> None:
    sw = ServerWrapper(model_cls=M, model_config=testrepo_config)

    class Fake:
        pass

    with pytest.raises(ValueError):
        sw.app = Fake()


@pytest.mark.asyncio
async def test_sw_app_is_none() -> None:
    sw = ServerWrapper(model_cls=M, model_config=testrepo_config)

    with pytest.raises(AttributeError):
        sw._app = None
        sw.app


@pytest.mark.asyncio
async def test_sw_set_model_cls_is_class_instance() -> None:
    m = M(testrepo_config)
    with pytest.raises(ValueError):
        ServerWrapper(model_cls=m, model_config=testrepo_config)


@pytest.mark.asyncio
async def test_sw_model_cls_is_none() -> None:
    sw = ServerWrapper(model_cls=M, model_config=testrepo_config)
    with pytest.raises(AttributeError):
        sw._model_cls = None
        sw.model_cls


@pytest.mark.asyncio
async def test_sw_model_is_none() -> None:
    sw = ServerWrapper(model_cls=M, model_config=testrepo_config)

    with pytest.raises(AttributeError):
        sw._model = None
        sw.model


@pytest.mark.asyncio
async def test_sw_set_model_is_invalid_type() -> None:
    sw = ServerWrapper(model_cls=M, model_config=testrepo_config)

    class Fake:
        pass

    with pytest.raises(ValueError):
        sw.model = Fake


def test_create_server() -> None:
    sw = create_server(M, testrepo_config)
    assert isinstance(sw, ServerWrapper)


class ServerWrapperTests(asynctest.TestCase):
    async def setUp(self) -> None:
        """Bring the server up"""
        self.server = create_server(M, testrepo_config)
        self.proc = multiprocessing.Process(target=self.server.start, daemon=True)
        self.proc.start()
        await asyncio.sleep(0.5)

    async def tearDown(self) -> None:
        self.proc.terminate()
        self.server = None

    async def test_root_route(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/") as resp:
                data = await resp.json()
                self.assertEqual(resp.status, 200)
        self.assertEqual(data, "This is root!")

    async def test_infer_route(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8000/infer", data='{"i": "1"}'
            ) as resp:
                data = await resp.json()
                self.assertEqual(resp.status, 200)
        self.assertEqual(data, "ba1")
