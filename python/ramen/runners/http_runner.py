import time
from typing import Any, Dict, Union

import uvicorn
from fastapi import FastAPI, Request, Response, status

from ramen.core import BaseRunner, ModelStates, ModelWrapper
from ramen.exceptions import FailedExecutionException
from logging import Logger


class HTTPRunner(BaseRunner):
    RUN_MODE: str = "http"

    def __init__(
        self,
        model_name: str,
        modelcls: ModelWrapper,
        model_args: Dict[str, Any],
        logger: Union[None, Logger] = None,
        enable_uvloop: bool = False,
        host: str = "0.0.0.0",
        port: int = 8000,
        logging_config: Union[Dict[str, Any], None] = None,
    ) -> None:
        super().__init__(HTTPRunner.RUN_MODE, modelcls, model_args, logger, enable_uvloop)
        self.model_name = model_name
        self.host = host
        self.port = port
        self.logging_config = uvicorn.config.LOGGING_CONFIG
        if logging_config is not None:
            assert all(
                key in logging_config for key in ["formatters", "handlers", "loggers"]
            )
            self.logging_config["formatters"].update(logging_config["formatters"])
            self.logging_config["handlers"].update(logging_config["handlers"])
            self.logging_config["loggers"].update(logging_config["loggers"])

    def failure(
        self,
        exc: Union[Exception, FailedExecutionException],
        data: Dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:

        if self._dexter_clb_url is None:
            self._logger.warning("`ORCHESTRATOR_URL` is not set, hence not firing callback")
        else:
            _ = self._fire_callback(
                state=ModelStates.FAILED, id=data["id"], logs=data["logs"]
            )
        self._logger.error(f"Failure: {exc}")

        if not hasattr(exc, "http_status_code"):
            status_code = 500
        else:
            if exc.http_status_code == 400:  # type: ignore
                status_code = status.HTTP_400_BAD_REQUEST
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        response: Response = Response(
            content=f"status code: {status_code} message:{exc}",
            status_code=status_code,
        )
        return response

    def success(
        self,
        data: Dict[str, Any],
    ) -> Any:
        if self._dexter_clb_url is None:
            self._logger.warning("`ORCHESTRATOR_URL` is not set, hence not firing callback")
        else:
            _ = self._fire_callback(
                state=ModelStates.COMPLETED,
                id=data["id"],
                result=data["result"],
                logs=data["logs"],
            )
        self._logger.info(f"Success: {data}")
        response: Response = Response(
            content=data["result"],
            headers={"Content-type": "application/json"},
            status_code=status.HTTP_200_OK,
        )
        return response

    @staticmethod
    async def root_path() -> str:
        return "This is root!"

    async def infer_path(self, request: Request) -> Any:
        body = await request.json()
        result = self.run_model_inference(body, request)
        return result

    def _init_fastapi_app(self) -> None:
        self._app = FastAPI()
        self._app.add_api_route("/", self.root_path, methods=["GET"])  # type: ignore
        self._app.add_api_route(
            "/infer", self.infer_path, response_class=Response, methods=["POST"]
        )

    def start(self, *args: Any, **kwargs: Any) -> None:
        try:

            self._init_model()
            self._init_model_inference_event_loop()
        except Exception as exc:

            self._logger.error(exc)
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            time.sleep(2)
            self._logger.info(f"Event loop running status: {self._loop.is_running()}")
            self._logger.info(f"thread alive status: {self._t.is_alive()}")
            raise exc
        self._init_fastapi_app()
        uvicorn.run(
            self._app,
            host=self.host,
            port=self.port,
            log_config=self.logging_config,
        )
