import inspect
import typing

import uvicorn
from fastapi import FastAPI, Request

from ramen.core import ModelWrapper


class ServerWrapper:
    def __init__(
        self,
        model_cls: ModelWrapper,
        model_config: str,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> None:
        self.host = host
        self.port = port
        self.model_cls = model_cls
        self._init_model(model_config)
        self._init_fastapi_app()

    @property
    def app(self) -> FastAPI:
        _app = getattr(self, "_app", None)
        if _app is None:
            raise AttributeError("FastAPI app has not been set")
        return _app

    @app.setter
    def app(self, value: FastAPI) -> None:
        if not isinstance(value, FastAPI):
            raise ValueError(
                f"`app` value needs to be of `FastAPI` type. Found to be {type(value)}"
            )
        self._app = value

    @property
    def model_cls(self) -> ModelWrapper:
        _model_cls = getattr(self, "_model_cls", None)
        if _model_cls is None:
            raise AttributeError("`model_cls` has not been provided")
        return _model_cls

    @model_cls.setter
    def model_cls(self, value: ModelWrapper) -> None:
        if not inspect.isclass(value):
            raise ValueError(
                f"`value` of type {type(value)} is instantiated. "
                "Pass an uninstantiated class"
            )
        self._model_cls = value

    @property
    def model(self) -> ModelWrapper:
        _model = getattr(self, "_model", None)
        if _model is None:
            raise AttributeError("`model` has not been provided")
        return _model

    @model.setter
    def model(self, value: ModelWrapper) -> None:
        if not isinstance(value, ModelWrapper):
            raise ValueError(
                f"`value` of type {type(value)} is invalid."
                " It should be of `ModelWrapper` type or a subclass of it"
            )
        self._model = value

    @staticmethod
    async def root_path() -> str:
        return "This is root!"

    @staticmethod
    async def infer_path(request: Request) -> None:
        body = await request.json()
        resp = await request.app.state.model.infer(body)
        return resp

    @typing.no_type_check
    def _init_model(self, model_config: str) -> None:
        self.model = self.model_cls(model_config)

    def _init_fastapi_app(self) -> None:
        self._app = FastAPI()
        self._app.add_api_route(
            "/", ServerWrapper.root_path, methods=["GET"]  # type: ignore
        )
        self._app.add_api_route(
            "/infer", ServerWrapper.infer_path, methods=["POST"]  # type: ignore
        )
        self._app.state.model = self._model

    def start(self) -> None:
        uvicorn.run(self._app, host=self.host, port=self.port)


def create_server(model: ModelWrapper, model_config: str) -> ServerWrapper:
    return ServerWrapper(model, model_config)
