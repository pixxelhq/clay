import asyncio
import json
import logging
import os
import time
from logging import Logger
from types import SimpleNamespace
from typing import Any, Dict, Final, List, Optional, Type, Union
import jq

import datatypes

from clay import type_utils, types, utils
from clay.callback import CallbackInterface, ErrorType, HTTPCallback
from clay.core import BaseRunner, ModelWrapper
from clay.exceptions import FailedExecutionException
from clay.logger import ClayLogger
from clay.storage.fs import process_input_list, process_output_list, process_spec_files
from clay.types import ModelStates
from clay.utils import yaml_to_namespace, get_current_utc_time_iso, get_value, Converters, cast_inputs
from clay import __version__ as clay_version


class RunnerConfig:
    # Environment variable keys
    _execution_id_env_key: Final[str] = "EXECUTION_ID"
    _input_json_env_key: Final[str] = "INPUT_JSON_ENV_KEY"
    _input_json_jq_filter_env_key: Final[str] = "INPUT_JSON_JQ_FILTER"
    _get_local_artifact_download_path_env_key: Final[str] = "LOCAL_ARTIFACT_DOWNLOAD_PATH"
    _remote_output_path_env_key: Final[str] = "REMOTE_OUTPUT_PATH"
    _remote_input_path_env_key: Final[str] = "REMOTE_INPUT_PATH"
    _force_input_types_to_v2_env_key: Final[str] = "FORCE_INPUT_TYPES_TO_V2"
    _callback_endpoint_env_key: Final[str] = "CALLBACK_ENDPOINT"
    _callback_headers_env_key: Final[str] = "CALLBACK_HEADERS"
    _output_json_path_env_key: Final[str] = "OUTPUT_JSON_PATH"
    _output_json_base_file_name_env_key: Final[str] = "OUTPUT_JSON_BASE_FILE_NAME"

    # Parameters with default values
    _execution_id: str = "default_execution_id"
    _input_json: List[Dict[str, Any]] = [{}]
    _input_json_jq_filter: Optional[str] = None
    _get_local_artifact_download_path: str = "/tmp/inputs"
    _remote_output_path: str = "/tmp/clay/outputs"
    _remote_input_path: str = "/tmp/clay/inputs"
    _force_input_types_to_v2: bool = False
    _config: Optional[Dict[str, Any]]
    _model_config: SimpleNamespace = {}  # type: ignore
    _callback_endpoint: str
    _callback_headers: Dict[str, str] = {}
    _callback_handler: CallbackInterface
    _outputs_json_path = "/tmp/clay/outputs/"
    _outputs_json_base_file_name = "spec.json"

    def __init__(
            self,
            config_path: str = "config.yaml"
    ) -> None:
        self._execution_id = os.getenv(self._execution_id_env_key, self._execution_id)
        self._input_json_string: str = os.getenv(os.getenv(self._input_json_env_key, "INPUT_JSON"), "[{}]")
        self._input_json: List[Dict[str, Any]] = None  # type: ignore
        self._input_json_jq_filter = os.getenv(self._input_json_jq_filter_env_key, None)
        self._get_local_artifact_download_path = os.getenv(self._get_local_artifact_download_path_env_key,
                                                           "/tmp/inputs")
        self._force_input_types_to_v2 = os.getenv("FORCE_INPUT_TYPES_TO_V2", "false").lower() == "true"
        self._model_config = yaml_to_namespace(config_path)
        self._callback_endpoint = os.getenv(self._callback_endpoint_env_key, "http://localhost:3000/callback")
        self._callback_headers = json.loads(os.getenv(self._callback_headers_env_key, "{}"))
        self._remote_output_path = os.getenv(self._remote_output_path_env_key, "/tmp/clay/outputs")
        self._remote_input_path = os.getenv(self._remote_input_path_env_key, "/tmp/clay/outputs")
        self._outputs_json_path = os.getenv(self._output_json_path_env_key, self._outputs_json_path)
        self._outputs_json_base_file_name = os.getenv(self._output_json_base_file_name_env_key,
                                                      self._outputs_json_base_file_name)

    def _process_input_json(self) -> None:
        if self._input_json is None:
            if self._input_json_jq_filter:
                try:
                    self._input_json = json.loads(
                        jq.compile(self._input_json_jq_filter).input(json.loads(self._input_json_string)).text())
                except Exception as e:
                    raise ValueError(f"Failed to process input JSON with jq filter '{self._input_json_jq_filter}': {e}")
            else:
                self._input_json = json.loads(self._input_json_string)

        # this is a hack to ensure that the input JSON always has the correct types, as argo might send
        # float as string
        for inp in self._input_json:
            inp["value"] = cast_inputs(inp["value"], inp["type"])

    def get_input_json(self) -> List[Dict[str, Any]]:
        self._process_input_json()
        return self._input_json

    def should_use_v2_input_types(self) -> bool:
        return self._force_input_types_to_v2

    def get_local_artifact_download_path(self) -> str:
        return self._get_local_artifact_download_path

    def get_model_config(self) -> SimpleNamespace:
        return self._model_config

    def get_callback_endpoint(self) -> str:
        return self._callback_endpoint

    def get_callback_headers(self) -> Dict[str, str]:
        return self._callback_headers

    def get_execution_id(self) -> str:
        return self._execution_id

    def get_remote_output_path(self) -> str:
        return self._remote_output_path

    def get_outputs_list_json_path(self) -> str:
        return self._outputs_json_path

    def get_outputs_json_base_file_name(self) -> str:
        return self._outputs_json_base_file_name

    def get_remote_input_path(self) -> str:
        return self._remote_input_path


class JobRunner(BaseRunner):
    def __init__(
            self,
            model_name: str,
            model_class: Type[ModelWrapper],
            model_args: Dict[str, Any],
            cfg_path: str,
            logger: Optional[Logger] = None,
            running_locally: bool = True,
    ) -> None:
        self._params = RunnerConfig(config_path=cfg_path)
        self._model_name: str = model_name
        self._inputs: Dict[str, datatypes.DataWrapperInterface] = {}
        self._model_class: Type[ModelWrapper] = model_class
        self._running_locally: bool = running_locally
        self._model_args: Dict[str, Any] = model_args
        self._model: ModelWrapper
        self._callback_handler: CallbackInterface = HTTPCallback(
            callback_endpoint=self._params.get_callback_endpoint(),
            headers=self._params.get_callback_headers(),
            retry_total=3,
            retry_backoff_factor=0.2,
            retry_status_forcelist=[500, 502, 503, 504],
        )
        self._start_time: str
        self._inference_output: List[datatypes.DataWrapperInterface] = []
        self._current_progress: float = 0.0
        self._output_dict: List[Dict[str, Any]] = None  # type: ignore
        self._input_dict: List[Dict[str, Any]] = []  # type: ignore

        if logger is None:
            log_level = logging.DEBUG if self._running_locally else logging.INFO
            logger = ClayLogger(
                logger_name=self._model_name,
                propagate=True,
                level=log_level,
            )
        assert isinstance(logger, Logger)
        self._logger: Logger = logger

    def _init_model(self) -> None:
        self.logger.info("initializing model constructor")
        self._model: ModelWrapper = self._model_class(**self._model_args)
        self.logger.info("initializing model constructor completed")
        self._model.set_progress = self.set_progress
        self._model.get_progress = self.get_progress
        self._model.add_progress = self.add_progress

    def _input_json_to_data_types(self, input_json: List[Dict[str, Any]]) -> None:
        inputs: Dict[str, datatypes.DataWrapperInterface] = {}
        input_config_dict = utils.convert_list_to_dict(self._params.get_model_config().inputs, "name")
        for input_data in input_json:
            typed_input: datatypes.DataWrapperInterface = type_utils.TypeFromDict(input_data, True)
            if typed_input.get_format() == types.FormatTypes.RASTER.value and not typed_input.get_field("stac_url"):
                typed_input.set_field("stac_url", input_config_dict[typed_input.get_name()].get("default", ""))
            if typed_input.get_value() == "":
                typed_input.set_value(input_config_dict[typed_input.get_name()].get("default", ""))
            inputs[input_data["name"]] = typed_input
        self._inputs = inputs

    def _collect_inputs(self, inputs: Optional[List[Dict[str, Any]]] = None) -> None:
        self.logger.info("parsing inputs")
        self._input_json_to_data_types(self._params.get_input_json())

        # this is a hack to ensure that the input JSON always has the correct types if version is not used
        for input_obj in self._inputs.values():
            self._input_dict.append(input_obj.serialize_to_dict())

        self.logger.info("processing input artifacts")
        self._inputs = process_input_list(self._inputs, self._params.get_local_artifact_download_path(),
                                          self._params.get_remote_input_path())
        self.logger.info("processing input artifacts completed")

    def output(self, key: str, value: Union[str, int, float], properties: Optional[
        Union[
            types.RasterProperties,
            types.VectorProperties,
            types.DateProperties,
            types.TabularProperties,
            Dict[str, Any],
        ]
    ] = None) -> None:
        pass

    def run_model_inference(self, *args: Any, **kwargs: Any) -> Any:
        pass

    def success(self) -> Any:
        self._logger.info("sending callback for success")
        self._callback_handler.send(
            id=self._params.get_execution_id(),
            outputs=self._get_output_list(),
            metadata={},
            logger=self._logger,
            progress=100,
            start_time=self._start_time,
            end_time=get_current_utc_time_iso(),
            status=ModelStates.COMPLETED
        )

    def failure(
            self,
            exc: Union[Exception, FailedExecutionException],
            data: Optional[Dict[str, Any]] = None,
            *args: Any,
            **kwargs: Any
    ) -> Any:
        err_msg = ""
        failure_type = ErrorType.RUNTIME_EXCEPTION
        if isinstance(exc, FailedExecutionException):
            err_msg = exc.msg
            failure_type = ErrorType.BAD_REQUEST

        self._callback_handler.send(
            id=self._params.get_execution_id(),
            metadata={},
            logger=self._logger,
            progress=100,
            start_time=self._start_time,
            end_time=get_current_utc_time_iso(),
            failure_type=failure_type,
            err_msg=err_msg,
            status=ModelStates.FAILED
        )

    def _flush_output_buffer(self, output_buffer: List[datatypes.DataWrapperInterface]) -> None:
        pass

    def _get_output_list(self) -> List[Dict[str, Any]]:
        if self._output_dict is not None:
            return self._output_dict

        output_dict: List[Dict[str, Any]] = []
        for output in self._inference_output:
            output_dict.append(output.serialize_to_dict())
        self._output_dict = output_dict
        return output_dict

    def _create_output_json_files(self) -> None:
        """Create JSON files for each output in the format: _outputs_json_base_file_name/{name}/spec.json"""
        for output in self._get_output_list():
            output_name = output.get("name")
            if output_name:
                output_dir = os.path.join(self._params.get_outputs_list_json_path(), output_name)
                os.makedirs(output_dir, exist_ok=True)

                spec_file_path = os.path.join(output_dir, self._params.get_outputs_json_base_file_name())
                with open(spec_file_path, 'w') as f:
                    json.dump(output, f, indent=2)

                self._logger.info(f"Created output spec file: {spec_file_path}")
                process_spec_files(spec_file_path, self._params.get_remote_output_path(), output_name)

    def get_progress(self) -> float:
        return self._current_progress

    def add_progress(self, progress_delta: float) -> None:
        if not (0 <= progress_delta <= 100):
            self._logger.error("Progress delta must be between 0 and 100.")
            return

        self._current_progress += progress_delta
        if self._current_progress > 100:
            self.logger.error("progress_delta cannot be set to a value higher than the max progress")
            return None

        self.set_progress(self._current_progress)

    def set_progress(self, progress: float) -> None:
        self._current_progress = progress
        self._callback_handler.send(
            id=self._params.get_execution_id(),
            metadata={},
            logger=self._logger,
            progress=progress,
            start_time=self._start_time,
        )

    def start(self, **kwargs: Any) -> None:
        self._logger.info("Starting Clay job runner version: %s", clay_version.__VERSION__)
        self._start_time = get_current_utc_time_iso()

        self._init_model()
        self._collect_inputs()

        self._callback_handler.send(
            id=self._params.get_execution_id(),
            inputs=self._input_dict,
            metadata={},
            logger=self._logger,
            progress=0,
            start_time=self._start_time,
        )

        try:
            result = asyncio.get_event_loop().run_until_complete(self._model.infer(inputs=self._inputs, opts=None))
            wrapped_result = type_utils.WrapTypes(result._outputs_buffer, True)
            output_dict: Dict[str, datatypes.DataWrapperInterface] = {}
            self._inference_output = wrapped_result  # type: ignore
            for output in self._inference_output:
                if not isinstance(output, datatypes.DataWrapperInterface):
                    raise TypeError(f"Expected DataWrapperInterface, got {type(output)}")

                metadata = output.get_field("metadata")
                if isinstance(metadata, dict):
                    metadata["block-name"] = self._model_name
                else:
                    metadata = {"block-name": self._model_name}
                output.set_field("metadata", metadata)

                output_dict[output.get_name()] = output  # type: ignore
            output_dict = process_output_list(output_dict, self._params.get_remote_output_path())
            for output_obj in self._inference_output:
                output_obj.set_value(output_dict[output_obj.get_name()].get_value())
            self.success()
            self._create_output_json_files()

        except Exception as exc:
            self._logger.error(exc)
            if exc is not None:
                self.failure(exc=exc)

            raise exc
