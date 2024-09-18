import asyncio
import json
import os
import pathlib
import shutil
import time
from collections import defaultdict
from enum import Enum
from logging import Logger
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from s3fs import S3FileSystem

import clay
from clay import _network, types
from clay.core import DATA_SPEC_FILENAME, BaseRunner, ModelWrapperType, ValueTypes, callback_wrapper
from clay.exceptions import FailedExecutionException, OutputOverwriteException
from clay.utils import (
    cast_inputs,
    convert_list_to_dict,
    get_current_utc_time_iso,
    get_filename_from_remote,
    get_io_name_to_dir_map,
    try_json_loads,
)


class _InjectedEnvVars(Enum):
    TaskId = "TASK_ID"
    TaskName = "TASK_NAME"
    WorkingDir = "WORKING_DIR"
    InputsWorkingDir = "INPUTS_WORKING_DIR"
    InputsRemotePath = "INPUTS_REMOTE_PATH"
    OutputsWorkingDir = "OUTPUTS_WORKING_DIR"
    OutputsRemotePath = "OUTPUTS_REMOTE_PATH"
    Env = "ENV"
    BlockName = "BLOCK_NAME"


_InjectedEnvVarsDefaults = {_InjectedEnvVars.OutputsRemotePath: ""}


class _ArgoConfEnvVars(Enum):
    ArgoTemplate = "ARGO_TEMPLATE"


REQUIRED_ENVVAR = set(
    [
        _InjectedEnvVars.TaskId,
        _InjectedEnvVars.WorkingDir,
        _InjectedEnvVars.InputsWorkingDir,
        _InjectedEnvVars.OutputsWorkingDir,
        _InjectedEnvVars.OutputsRemotePath,
    ]
)


class JobRunnerV2(BaseRunner):
    """Runner that executes the model in `argo` execution mode. The only situation in which
    this runner would be used, is if the model is part of a workflow.

    This implements support of executing argo workflow nodes.

    Args:
        BaseRunner (_type_): _description_

    Raises:
        FileNotFoundError: _description_
        OutputOverwriteException: _description_
        ValueError: _description_
        ValueError: _description_
        exc: _description_

    Returns:
        _type_: _description_
    """

    RUN_MODE: str = "argo"

    def __init__(
        self,
        model_name: str,
        modelcls: Type[ModelWrapperType],
        model_args: Dict[str, Any],
        cfg_path: str,
        logger: Union[Logger, None] = None,
        enable_uvloop: bool = False,
        enable_debug_logs: bool = False,
    ) -> None:
        super().__init__(JobRunnerV2.RUN_MODE, modelcls, model_args, cfg_path, logger, enable_uvloop, enable_debug_logs)
        self.model_name = model_name
        self._injected_envvars: Dict[_InjectedEnvVars, Any] = {}
        self._inputs_prop_map: Dict[str, Any] = defaultdict(None)
        self._inputs_list: List[Dict[str, Any]] = []
        self._passed_inputs_dict: Dict[str, Any] = {}
        self._outputs_list: List[Dict[str, Any]] = []
        self._param_outputs_local_remote_path_maping: List[Tuple[str, str]]

        self.expected_outputs = dict((oi["name"], oi) for oi in self.config.outputs)
        self._model_outputs_dict: Dict[str, Any] = {}
        self._output_keys_written: Set[str] = set()

        self._s3fs = S3FileSystem()
        # Dict rep of https://argoproj.github.io/argo-workflows/fields/#template
        self._argo_template_spec: Dict[str, Any] = {}

        # self._manual_s3_sync_list: List[Tuple[]]

    def get_injected_envvar_if_found(self, key: _InjectedEnvVars) -> Tuple[str, bool]:
        val = self._injected_envvars.get(key)
        if val is None:
            return "", False
        return val, True

    def set_injected_envvar(self, key: _InjectedEnvVars, val: Any) -> None:
        self._injected_envvars[key] = val

    def read_injected_envvars(self) -> None:
        for e in _InjectedEnvVars:
            val = os.getenv(e.value) or _InjectedEnvVarsDefaults.get(e, None)
            if val is None:
                if e in REQUIRED_ENVVAR:
                    # checking if there are any defaults set
                    if e in _InjectedEnvVarsDefaults:
                        self.set_injected_envvar(e, _InjectedEnvVarsDefaults[e])
                    else:
                        err = LookupError(
                            f"Missing required configuration: required environment variable not found: `{e.name}`"
                        )
                        self.logger.error(err, exc_info=err)
                        raise err
                self.logger.debug(f"Environment variable not found: `{e.name}`")

            self.set_injected_envvar(e, val)

        # additionally reading argo related env fields
        self._read_argo_template_spec()

    def set_inputs_propmap(self, key: str, value: Dict[Any, Any]) -> None:
        self._inputs_prop_map[key] = value

    def get_inputs_propmap(self, key: Union[str, None]) -> Union[Dict[Any, Any], Dict[str, Any]]:
        # If key is None, then it returns the entire dict
        if key is None:
            return self._inputs_prop_map
        return self._inputs_prop_map[key]

    def update_inputs_list(self, value: Dict[str, Any]) -> None:
        self._inputs_list.append(value)

    def get_inputs_list(self) -> List[Dict[str, Any]]:
        return self._inputs_list

    def update_outputs_list(self, value: Dict[str, Any]) -> None:
        self._outputs_list.append(value)

    def get_outputs_list(self) -> List[Dict[str, Any]]:
        return self._outputs_list

    def update_passed_inputs_dict(self, key: str, value: Any) -> None:
        self._passed_inputs_dict[key] = value

    def get_passed_inputs_dict(self, key: Optional[str] = None) -> Union[Any, Dict[str, Any]]:
        if key is None:
            return self._passed_inputs_dict
        return self._passed_inputs_dict[key]

    def update_model_outputs_dict(self, key: str, value: Any) -> None:
        self._model_outputs_dict[key] = value

    def get_model_outputs_dict(self, key: Optional[str] = None) -> Union[Any, Dict[str, Any]]:
        if key is None:
            return self._model_outputs_dict
        return self._model_outputs_dict[key]

    def _read_argo_template_spec(self) -> None:
        s = os.getenv(_ArgoConfEnvVars.ArgoTemplate.value)
        if s is None:
            if self.enable_debug_logs:
                self.logger.warning(f"Could not read {_ArgoConfEnvVars.ArgoTemplate.value} from env")
            return
        self._argo_template_spec = json.loads(s)

    def _handle_parameter_input(self, name: str, value: Any, input_cfg: Dict[str, Any]) -> Any:
        model: types.Data = types._FormatModelMap[input_cfg["format"]].model_validate(input_cfg)
        model.Value = value
        # wtf to do here?

    def _handle_artifact_input(self, name: str, value: Any, value_type: Any) -> Any:
        pass

    # The `None` assignment is to statisfy the type checker
    def _collect_inputs(
        self, inputs: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[Dict[str, types.Data], Dict[str, Any]]:
        def extract_input_parameters_from_argo_template() -> Dict[str, Any]:
            argo_inputs = self._argo_template_spec.get("inputs", {})
            if "parameters" in argo_inputs:
                return convert_list_to_dict(argo_inputs["parameters"], "name")
            return {}

        def get_workflow_input_directory() -> str:
            input_working_dir, _ = self.get_injected_envvar_if_found(_InjectedEnvVars.InputsWorkingDir)
            return input_working_dir

        def is_artifact_input(input_config: Dict[str, Any]) -> bool:
            return input_config.get(types._IS_ARTIFACT_ATTR_NAME, False)

        def process_artifact_input(input_config: Dict[str, Any], input_dirmap: Dict[str, str]) -> Tuple[Dict[str, Any], types.Data]:
            path = input_dirmap.get(input_config["name"])
            if path is None:
                clay.failure(f"`{input_config['name']}` not found")

            with open(os.path.join(path, DATA_SPEC_FILENAME)) as f: # type: ignore
                spec = json.load(f)
            spec["name"] = input_config["name"]
            self.update_inputs_list(spec.copy())

            value = cast_inputs(spec["value"], spec["type"])
            if spec["type"] == ValueTypes.URL.value:
                filename = get_filename_from_remote(value)
                value = os.path.join(path, filename) # type: ignore

            spec["value"] = value
            data = types._FormatModelMap[input_config["format"]].model_validate(spec)

            return spec, data

        def process_parameter_input(input_config: Dict[str, Any], input_parameters: Dict[str, Any], input_working_dir: str) -> Tuple[Dict[str, Any], types.Data]:
            value = input_parameters.get(input_config["name"], {}).get("value", None) or input_config.get("value")
            value = self.extract_parameter_value(value) # type: ignore
            value = cast_inputs(value, input_config["type"])

            input_config["value"] = value
            data = types._FormatModelMap[input_config["format"]].model_validate(input_config)

            data_dict = data.model_dump(by_alias=True)
            spec_path = pathlib.Path(os.path.join(input_working_dir, input_config["name"]))
            spec_path.mkdir(exist_ok=True, parents=True)
            with open(os.path.join(spec_path, DATA_SPEC_FILENAME), "w+") as f:
                json.dump(data_dict, f)

            return input_config, data

        input_parameters = extract_input_parameters_from_argo_template()
        input_specs, typed_inputs = {}, {}
        input_base_directory = get_workflow_input_directory()
        input_name_to_dir_map = get_io_name_to_dir_map(self.config.inputs, input_base_directory)

        for input_config in self.config.inputs:
            if is_artifact_input(input_config):
                spec, data = process_artifact_input(input_config, input_name_to_dir_map)
            else:
                spec, data = process_parameter_input(input_config, input_parameters, input_base_directory)

            typed_inputs[input_config["name"]] = data
            input_specs[input_config["name"]] = spec
            self.set_inputs_propmap(input_config["name"], spec)
            self.update_inputs_list(spec)
            self.update_passed_inputs_dict(input_config["name"], spec["value"])

        return typed_inputs, input_specs

    def extract_parameter_value(self, value: str) -> str:
        value_if_dict = try_json_loads(value)
        if value_if_dict is not None:
            value = value_if_dict
        return value

    def _handle_output_asset(self, key: str, value_type: ValueTypes, src: str, named_output_dir: str) -> str:
        """takes a file that is to become an output asset and moves it to the correct
        place. Please note,
        currently only single files are supported.

        Args:
            key (str): The name of the output parameter
            value_type (ValueTypes): The type of value in the output parameter
            file_path (str): Path to the local file
            output_working_dir (str): Output directory for the named output parameter

        Returns:
            str: The remote path of the asset
        """
        asset_log_dict = {
            "asset_key": key,
            "asset_value_type": value_type,
            "asset_source": src,
            "output_directory": named_output_dir,
        }
        self.logger.debug(f"Handling output asset: {asset_log_dict}")
        # replaces any preexisting files
        if not os.path.exists(src):
            raise FileNotFoundError(f"cannot find src file `{src}`")
        file_name = os.path.basename(src)
        _ = shutil.copy(src, os.path.join(named_output_dir, file_name))
        assert os.path.exists(os.path.join(named_output_dir, file_name))
        remote_path, found = self.get_injected_envvar_if_found(_InjectedEnvVars.OutputsRemotePath)
        remote_path = os.path.join(remote_path, key, file_name)
        return remote_path

    def _upload_parameter_output_spec_file(self, data_item_name: str, local_spec_file_path: str) -> None:
        file_name = os.path.basename(local_spec_file_path)
        remote_path, found = self.get_injected_envvar_if_found(_InjectedEnvVars.OutputsRemotePath)
        if not found or remote_path == "":
            self.logger.error("cannot upload parameter output spec files since `OUTPUTS_REMOTE_PATH` is not send")
            return None
        remote_path = os.path.join(remote_path, data_item_name, file_name)
        self.logger.info(f"starting to upload {local_spec_file_path} to {remote_path}")
        self._s3fs.put_file(local_spec_file_path, remote_path)
        self.logger.info("upload complete")

    def _output_handler(self, data: types.Data) -> None:
        """Set an output asset. This method is responsible for creating the necessary
        output jsons and moving any required asset to its correct location without any
        intervention from the user.

        Please note, that as of now, only primitive data types are support in the value
        parameter. Meaning, the type of value parameter can only be one of the primitive
        types as defined in the type definition. Going forward, we might have format
        based handlers, but thats a story for another time.

        Another important thing to note is properties. Properties are `format` specific.
        Each `format` may or may not define a set of properties. Hence, since each output
        item of a model has a `format`, the output item may or may not have properties.
        This can lead to 3 scenarios that a model dev need's to worry about,

        1. `properties` is set to `None` (default)

        In this case, clay would automatically fill the output item with properties as
        defined in the model spec file.

        2. `properties` is set to one of the `XXXProperties` types defined in `clay.types`

        In this case, clay would ensure that the output json has properties as defined by
        the user during runtime. Please note, we don't validate for any logical fallacies
        in the user provided properties at runtime. So use this carefully!

        When should one use this? Ideally, this behaviour is to be used by model devs in
        situationscwherein they need to manually set the properties of some output object.

        3. `properties` can be an arbitary dict.

        Please note, this is **extremely unsafe operation** with possibly a whole lot of
        unknown side-effects. Use this only at if there is no other options and the world
        would come crashing down otherwise.

        Args:
            key (str): Name of the output parameter
            value (Union[
                types.URL,
                types.Str,
                types.Int,
                types.Float,
            ]):
                The actual value of the output parameter.

        properties (
                Optional[
                        Union[
                            types.RasterProperties,
                            types.VectorProperties,
                            types.DateProperties,
                            types.TabularProperties,
                            Dict[str, Any],
                        ]
                ],
                optional
            ):
                Properties to be assigned to the output type. Defaults to None.

        Raises:
            OutputOverwriteException: exception raised when the user attempts to
            overwrite an already written output file.
        """

        if data.Name not in self.expected_outputs:
            self.logger.error(f"`{data.Name}` is not listed as an expected output in the config/specification file.")
            return

        if data.Name in self._output_keys_written:
            self.logger.error(
                f"Received output for `{data.Name}` again. Please ensure each output is returned only once."
            )
            raise OutputOverwriteException(f"Duplicate output received for `{data.Name}`")

        output_config = self.expected_outputs[data.Name]
        _format = output_config["format"]
        if data.Format != _format:
            raise ValueError(f"invalid format `{data.Format}` for `{data.Name}`. Expected `{_format}`")

        # set `displayName` and `description` from config
        data.DisplayName = output_config.get("display_name", "")
        data.Description = output_config.get("description", "")
        data.Group = output_config.get("group", "")

        # add block-name to metadata if available
        block_name, found = self.get_injected_envvar_if_found(_InjectedEnvVars.BlockName)
        if found:
            if data.Metadata:
                data.Metadata["block-name"] = block_name
            else:
                data.Metadata = {"block-name": block_name}

        output_working_dir, found = self.get_injected_envvar_if_found(_InjectedEnvVars.OutputsWorkingDir)
        named_output_dir = pathlib.Path(os.path.join(output_working_dir, data.Name))
        named_output_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
        assert os.path.exists(named_output_dir)
        self.logger.info(f"Asset info: {data}")
        self.logger.info(f"Asset output directory (`{data.Name}`): {named_output_dir}")

        # here we check if the output item in question is an artifact or not. If it
        # is not, then we dont process any supporting artifact file.
        if output_config["type"] == ValueTypes.URL.value or output_config.get(types._IS_ARTIFACT_ATTR_NAME, False):
            value = self._handle_output_asset(data.Name, ValueTypes.URL, str(data.Value), str(named_output_dir))
            data.Value = value

        # setting the type
        data.Type = output_config["type"]

        if hasattr(data, "Properties"):
            if "properties" not in output_config and data.Properties is not None:  # type: ignore
                raise ValueError(f"found properties for output `{data.Name}` but config has " "no properties set")
            elif "properties" in output_config and data.Properties is None:  # type: ignore
                data.Properties = types._PropertiesFromConfig(output_config)  # type: ignore

        # Note: `exclude_None` to be added only after careful testing since there are lot of side effects
        output = data.model_dump(by_alias=True)

        output_parameter_path = pathlib.Path(os.path.join(output_working_dir, data.Name))
        output_parameter_path.mkdir(mode=0o777, parents=True, exist_ok=True)

        self._output_keys_written.add(data.Name)
        self.update_model_outputs_dict(data.Name, data.Value)
        self.update_outputs_list(output)

        local_spec_file_path = output_parameter_path.joinpath(DATA_SPEC_FILENAME)
        with open(local_spec_file_path, "w+") as f:
            json.dump(output, f)

        if not data.IsArtifact:
            self._upload_parameter_output_spec_file(data.Name, str(local_spec_file_path))

    def _flush_output_buffer(self, output_buffer: types.OutputsBuffer) -> None:
        for val in output_buffer:
            self._output_handler(val)

    def _flush_input_buffer(self) -> None:
        local_input_path, found = self.get_injected_envvar_if_found(_InjectedEnvVars.InputsWorkingDir)
        if not found or local_input_path == "":
            self.logger.error("cannot upload input files since `INPUTS_WORKING_DIR` is not set")
            return None

        remote_input_path, found = self.get_injected_envvar_if_found(_InjectedEnvVars.InputsRemotePath)
        if not found or remote_input_path == "":
            self.logger.error("cannot upload input files since `INPUTS_REMOTE_PATH` is not set")
            return None

        self.logger.info(f"starting to upload {local_input_path} to {remote_input_path}")
        self._s3fs.put(local_input_path, remote_input_path, recursive=True)
        self.logger.info("upload complete")

    def success(self) -> None:
        task_id, found = self.get_injected_envvar_if_found(_InjectedEnvVars.TaskId)
        clb = types.Callback(
            Id=task_id, State=types.ModelStates.COMPLETED, Outputs=self.get_outputs_list(), Progress=100.0
        )
        success = self._model.send_callback(callback=clb)

        # We do it this way so that we can:
        # 1. Fire orchestrator logs only when we're not running locally
        # 2. Still maintain the correct log level
        if not success and self.enable_debug_logs:
            self.logger.error("FAILED: Could not fire Orchestrator callback")

    def failure(
        self,
        exc: Union[Exception, FailedExecutionException],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if self._dexter_clb_url is None:
            if self.enable_debug_logs:
                self.logger.warning("`ORCHESTRATOR_URL` is not set, hence not firing callback")
            return
        if isinstance(exc, FailedExecutionException):
            err_msg = exc.msg
            failure_type = types.FailureTypes.BADREQUEST.value
        else:
            err_msg = ""
            failure_type = types.FailureTypes.RUNTIME.value

        task_id, _ = self.get_injected_envvar_if_found(_InjectedEnvVars.TaskId)
        end_time = get_current_utc_time_iso()
        callback = types.Callback(
            Id=task_id,
            State=types.ModelStates.FAILED,
            ErrMsg=err_msg,
            EndTime=end_time,
            FailureType=failure_type,
            Progress=100,
        )
        self._model.send_callback(callback=callback)

        self.logger.info("Inference finished")
        raise exc

    def run_model_inference(self, *args: Any, **kwargs: Any) -> Tuple[types.OutputsBuffer, Optional[Exception]]:
        if "start_time" in kwargs:
            start_time = kwargs.get("start_time")
        else:
            self.logger.info("`start_time` not found in kwargs")
            start_time = get_current_utc_time_iso()

        typed_inputs, _ = self._collect_inputs()
        assert isinstance(typed_inputs, dict)

        self._flush_input_buffer()
        id, _ = self.get_injected_envvar_if_found(_InjectedEnvVars.TaskId)

        callback = types.Callback(
            Id=id, State=types.ModelStates.INPROGRESS, Inputs=self.get_inputs_list(), StartTime=start_time, Progress=5
        )
        # fire inprogress callback
        success = self._model.send_callback(callback=callback)

        if not success and self.enable_debug_logs:
            self.logger.error("FAILED: Could not fire Orchestrator callback")

        opts = types.InferenceOpts(
            Id=id,
            InputList=self.get_inputs_list(),
            InputPropMap=self.get_inputs_propmap(None),
        )
        self.logger.info("Inputs", typed_inputs)
        try:
            ctx = asyncio.run_coroutine_threadsafe(
                self._model.infer(inputs=typed_inputs, opts=opts),
                self._loop,
            ).result()
        except Exception as exc:
            self._model.logger.error(exc, exc_info=exc)
            return [], exc

        result = ctx.get_output_buffer()

        self._flush_output_buffer(result)

        inf_times = ctx.get_model_inf_times()
        end_time = get_current_utc_time_iso()
        serialized_result = types._serialize_output_buffer(result)
        clb = types.Callback(
            Id=id,
            State=types.ModelStates.COMPLETED,
            Result=serialized_result,
            BlockInfStartTime=inf_times.InfStartTime,
            BlockInfEndTime=inf_times.InfEndTime,
            EndTime=end_time,
            Progress=100,
        )
        success = self._model.send_callback(callback=clb)
        if not success and self.enable_debug_logs:
            self.logger.warning("FAILED: Could not fire Orchestrator callback")
        return result, None

    def start(self, **kwargs: Any) -> None:
        start_time = get_current_utc_time_iso()
        self.read_injected_envvars()
        try:
            self._init_model()
            self._init_model_inference_event_loop()
        except Exception as exc:
            self.logger.error(exc)
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            time.sleep(2)
            self.logger.debug(f"Event loop running status: {self._loop.is_running()}")
            self.logger.debug(f"thread alive status: {self._t.is_alive()}")

            task_id, _ = self.get_injected_envvar_if_found(_InjectedEnvVars.TaskId)
            clb = types.Callback(
                Id=task_id,
                State=types.ModelStates.FAILED,
                ErrMsg="internal server error",
            )
            _network._fire_callback_to_dexter(clb, self.logger, self._dexter_clb_url, self.enable_debug_logs)

        conn_params = {
            types._CommonEnvvars.DEXTER_HOST: self._dexter_host,
            types._CommonEnvvars.DEXTER_PORT: self._dexter_port,
            types._CommonEnvvars.ORCHESTRATOR_URL: self._dexter_clb_url,
            types._CommonEnvvars.TASK_ID: self.get_injected_envvar_if_found(_InjectedEnvVars.TaskId)[0],
        }
        callback_fn = callback_wrapper(conn_params)
        self._model.set_callback_callable(callback_fn)

        result, exc = self.run_model_inference(start_time=start_time)  # type: ignore
        if exc is not None:
            self.failure(exc)
        self.logger.info(f"Inference Results: {result}")
