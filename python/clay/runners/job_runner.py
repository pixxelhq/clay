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
from urllib3.util import parse_url

import clay
from clay import types, utils
from clay.core import DATA_SPEC_FILENAME, BaseRunner, ModelWrapper, ValueTypes
from clay.exceptions import FailedExecutionException, OutputOverwriteException

__LOCAL_WORKING_DIR__ = "/tmp"
__DEFAULT_AUTO_DOWNLOAD_ASSETS__ = False
__DEFAULT_AUTO_UPLOAD__ = True


class _InjectedEnvVars(Enum):
    ClbUrl = "ORCHESTRATOR_URL"
    AutoDownloadAssets = "AUTO_DOWNLOAD_ASSETS"
    DisableAutoUpload = "DISABLE_AUTO_UPLOAD"
    RemotePrefix = "REMOTE_PREFIX"


_InjectedEnvVarsDefaults = {
    _InjectedEnvVars.AutoDownloadAssets: __DEFAULT_AUTO_DOWNLOAD_ASSETS__,
    _InjectedEnvVars.DisableAutoUpload: __DEFAULT_AUTO_UPLOAD__,
}


class _ExpectedInfParameters(Enum):
    TaskId = "task-id"
    WorkflowId = "workflow-id"
    JobId = "job-id"
    RemotePrefix = "remote-prefix"
    LocalWorkingDir = "local-working-dir"


class JobRunner(BaseRunner):
    """Runner that executes the model in **job** mode. This is generally the case when the model
    is to be executed in isolation, meaning, the outputs of the models are not be fed into
    some other model execute sequentially.

    Mostly, a model running locally, on CI or on orchestrator in direct inference mode, would be using this
    runner.

    Ideally, the only place the model author would interact with the this class is when writing tests.

    !!! note

        We are planning to abstract that as well such that the `Run` function can be used even in tests.
    """

    RUN_MODE: str = "job"

    def __init__(
        self,
        model_name: str,
        modelcls: Type[ModelWrapper],
        model_args: Dict[str, Any],
        cfg_path: str,
        logger: Optional[Logger] = None,
        enable_uvloop: bool = False,
        enable_debug_logs: bool = False,
    ) -> None:
        """
        Args:
            model_name (str): Name of the model being run.
            modelcls (ModelWrapper):
                The `uninstantiated` model class.
            model_args (Dict[str, Any]):
                Arguments that are to be passed into the model. Almost always, it would be
                `{"cfg_path": "path/to/model/spec"}`. This is the result of an inconsistent
                design choice and would be removed soon.
            cfg_path (str): Path to the model spec file.
            logger (Optional[Logger], optional): Any custom logger. Defaults to None.
            enable_uvloop (bool, optional): Legacy, would be removed. Defaults to False.
        """
        super().__init__(JobRunner.RUN_MODE, modelcls, model_args, cfg_path, logger, enable_uvloop, enable_debug_logs)
        self.model_name = model_name
        self._injected_envvars: Dict[_InjectedEnvVars, Any] = {}

        self._inputs_prop_map: Dict[str, Any] = defaultdict(None)
        self._inputs_list: List[Dict[str, Any]] = []
        self._passed_inputs_dict: Dict[str, Any] = {}

        self._outputs_list: List[Dict[str, Any]] = []
        self.expected_outputs = dict((oi["name"], oi) for oi in self.config.outputs)
        self._model_outputs_dict: Dict[str, Any] = {}
        self._output_keys_written: Set[str] = set()

        self._inf_opts: Dict[_ExpectedInfParameters, str] = defaultdict(None)

        self._s3fs = S3FileSystem()

    def get_injected_envvar(self, key: _InjectedEnvVars) -> Tuple[str, bool]:
        val = self._injected_envvars.get(key)
        if val is None:
            return "", False
        return val, True

    def set_injected_envvar(self, key: _InjectedEnvVars, val: Optional[Union[bool, str]]) -> None:
        self._injected_envvars[key] = val

    def read_injected_envvars(self) -> None:
        for e in _InjectedEnvVars:
            val: Optional[Union[str, bool]] = os.getenv(e.value)
            if val is None and _InjectedEnvVarsDefaults.get(e) is None:
                continue
            elif val is None:
                val = _InjectedEnvVarsDefaults.get(e)
            # TODO: handle this better and cleaner
            assert val is not None
            if e == _InjectedEnvVars.AutoDownloadAssets and not isinstance(val, bool):
                val = json.loads(val)
            elif e == _InjectedEnvVars.DisableAutoUpload and not isinstance(val, bool):
                val = json.loads(val)
            self.set_injected_envvar(e, val)

    def update_model_outputs_dict(self, key: str, value: Any) -> None:
        self._model_outputs_dict[key] = value

    def get_model_outputs_dict(self, key: Optional[str] = None) -> Union[Any, Dict[str, Any]]:
        if key is None:
            return self._model_outputs_dict
        return self._model_outputs_dict[key]

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

    def _handle_input_assets(
        self,
        data: types.Data,
        named_input_dir: str,
        named_remote_output_dir: str,
    ) -> types.Data:
        if not self._injected_envvars[_InjectedEnvVars.AutoDownloadAssets]:
            return data
        if data.Type != ValueTypes.URL.value or not data.IsArtifact:
            return data

        if data.Type == ValueTypes.URL.value and data.Format == types.FormatTypes.VECTOR.value:
            return self._handle_vector_input_assets(data, named_input_dir)

        url_fragments = parse_url(str(data.Value))
        if url_fragments.scheme != "s3":
            self.logger.warning(f"Unknown scheme while parsing {data.Value}: {url_fragments.scheme}")
        file_name = os.path.basename(url_fragments.path)  # type: ignore
        local_path = pathlib.Path(named_input_dir, str(file_name))
        self._s3fs.get_file(data.Value, str(local_path))
        if not local_path.exists():
            raise FileNotFoundError(f"failed to find file {data.Value}")
        if named_remote_output_dir != "":
            named_remote_output_dir = os.path.join(named_remote_output_dir, str(file_name))
            if not self._injected_envvars[_InjectedEnvVars.DisableAutoUpload]:
                self.logger.info(f"Uploading {str(local_path)} to {named_remote_output_dir}")
                # TODO: here we risk overwriting the file if it exists. Ideally, if the
                # file exists in the named-remote-output-dir path, then we shouldnt upload
                try:
                    self._s3fs.info(named_remote_output_dir)
                    # the line below is run only if the file exists in the said path
                    self.logger.warning(f"File found at {named_remote_output_dir}. will be overwritten")
                except FileNotFoundError:
                    pass
                self._s3fs.put_file(str(local_path), named_remote_output_dir)
                self.logger.info(f"Finished uploading {local_path} to {named_remote_output_dir}")
        data.Value = str(local_path)
        return data

    def _handle_vector_input_assets(
        self,
        data: types.Data,
        named_input_dir: str,
    ) -> types.Data:  # type: ignore
        try:
            _ = parse_url(str(data.Value))
        except Exception as exc:
            self.logger.warn(f"unable to parse json: {exc}")
            # if the url is not parseable, then we assume it is a stringified geojson
            try:
                parsed_data = json.loads(str(data.Value))
                local_path = pathlib.Path(named_input_dir, os.path.basename("input.geojson"))
                with open(local_path, "w+") as f:
                    json.dump(parsed_data, f, indent=4)
                data.Value = str(local_path)
                self.logger.info("found stringified json")
            except json.JSONDecodeError:
                clay.failure("failed to parse geojson with value {0}".format(data.Value))
        return data

    def _backward_compatibility_missing_infparams(self) -> None:
        if self._inf_opts.get(_ExpectedInfParameters.WorkflowId) is None:
            wfid = os.getenv(_ExpectedInfParameters.WorkflowId.value)
            if wfid is None:
                raise ValueError(f"did not find `{_ExpectedInfParameters.WorkflowId.value}`")
            self._inf_opts[_ExpectedInfParameters.WorkflowId] = wfid
        if self._inf_opts.get(_ExpectedInfParameters.JobId) is None:
            jobid = os.getenv(_ExpectedInfParameters.JobId.value)
            if jobid is None:
                raise ValueError(f"did not find `{_ExpectedInfParameters.JobId.value}`")
            self._inf_opts[_ExpectedInfParameters.JobId] = jobid
        if self._inf_opts.get(_ExpectedInfParameters.LocalWorkingDir) is None:
            local_working_dir = os.getenv(_ExpectedInfParameters.LocalWorkingDir.value)
            if local_working_dir is None:
                raise ValueError(f"did not find `{_ExpectedInfParameters.LocalWorkingDir.value}`")
            self._inf_opts[_ExpectedInfParameters.LocalWorkingDir] = local_working_dir
            # The `None` assignment is to statisfy the type checker

    def _collect_inputs(
        self, inputs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Union[Dict[str, Any], Tuple[Dict[str, types.Data], Dict[str, Any]]]]:
        """Collects inputs. More details to be added"""
        # first we convert list of dicts to a dict of dicts
        if inputs is None:
            raise ValueError("inputs cannot be None")
        tmp = {}
        for i in inputs:
            tmp[i["name"]] = i
        dict_inputs = tmp
        # second we pop the parameters mentioned in `_InfOpts`
        for o in _ExpectedInfParameters:
            val, ke = utils.pop_dict_with_err(dict_inputs, o.value)
            if ke is not None:
                # TODO: make this an fatal error
                self.logger.debug(ke)
            if val is not None:
                self._inf_opts[o] = val.get("value")
                continue
            # self._inf_opts[o] = val
        self._backward_compatibility_missing_infparams()

        workflow_id = self._inf_opts[_ExpectedInfParameters.WorkflowId]
        job_id = self._inf_opts[_ExpectedInfParameters.JobId]
        task_id = self._inf_opts[_ExpectedInfParameters.TaskId]

        local_working_dir = self._inf_opts[_ExpectedInfParameters.LocalWorkingDir]
        input_working_dir = pathlib.Path(os.path.join(local_working_dir, workflow_id, job_id, task_id, "inputs"))
        input_working_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        input_config_dict = utils.convert_list_to_dict(self.config.inputs, "name")
        _processed_inputs = {}
        for k, v in dict_inputs.items():
            model: types.Data = types._FormatModelMap[v["format"]].model_validate(v)
            if model.Value is None:
                model.Value = input_config_dict[model.Name].get("default", None)
            named_input_dir = pathlib.Path(input_working_dir, model.Name)
            named_input_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

            remote_working_dir = ""
            named_remote_working_dir = ""
            remote_prefix, found = self.get_injected_envvar(_InjectedEnvVars.RemotePrefix)
            if found:
                remote_working_dir = os.path.join(remote_prefix, workflow_id, job_id, task_id, "inputs")

                named_remote_working_dir = os.path.join(remote_working_dir, model.Name)

            model = self._handle_input_assets(model, str(named_input_dir), named_remote_working_dir)

            i = model.model_dump(by_alias=True)
            with open(os.path.join(named_input_dir, DATA_SPEC_FILENAME), "w+") as f:
                json.dump(i, f)

            # uploading inputs to remote directory if allowed for parity with
            # argo executor
            if not self._injected_envvars[_InjectedEnvVars.DisableAutoUpload]:
                remote_path = os.path.join(named_remote_working_dir, DATA_SPEC_FILENAME)
                local_spec_file_path = os.path.join(named_input_dir, DATA_SPEC_FILENAME)
                self.logger.info(f"Uploading {local_spec_file_path} to {remote_path}")
                self._s3fs.put_file(local_spec_file_path, remote_path)
                self.logger.info("Finished uploading.")

            _processed_inputs[k] = model
            self._inputs_prop_map[k] = i["properties"] if "properties" in i else None
            self.update_inputs_list(i)
            self.update_passed_inputs_dict(k, i)
        return _processed_inputs, dict_inputs

    def _handle_output_asset(
        self,
        key: str,
        value_type: ValueTypes,
        src: str,
        named_output_dir: str,
        named_remote_output_dir: str,
    ) -> str:
        if not os.path.exists(src):
            raise FileNotFoundError(f"Cannot find source file `{src}`")
        file_name = os.path.basename(src)
        dest = os.path.join(named_output_dir, file_name)
        self.logger.info(f"Copying file: `{src}` to `{dest}`")
        _ = shutil.copy(src, dest)
        if named_remote_output_dir != "":
            named_remote_output_dir = os.path.join(named_remote_output_dir, file_name)
            # TODO: Upload to s3 here
            if not self._injected_envvars[_InjectedEnvVars.DisableAutoUpload]:
                self.logger.info(f"Uploading file: {dest} to {named_remote_output_dir}")
                self._s3fs.put_file(dest, named_remote_output_dir)
                self.logger.info("Finished Uploading")
            return named_remote_output_dir
        return dest

    def _output_handler(self, data: types.Data) -> None:
        """processes each output item. More details to be added."""
        if data.Name not in self.expected_outputs:
            self.logger.error(f"`{data.Name}` not found in outputs")
            return

        if data.Name in self._output_keys_written:
            self.logger.error(f"Rewriting output key: `{data.Name}`")
            raise OutputOverwriteException("attempting to overwrite output")

        output_config = self.expected_outputs[data.Name]
        _format = output_config["format"]
        if data.Format != _format:
            raise ValueError(f"invalid format `{data.Format}` for `{data.Name}")

        # set `displayName` and `description` from config
        data.DisplayName = output_config.get("display_name", "")
        data.Description = output_config.get("description", "")

        workflow_id = self._inf_opts[_ExpectedInfParameters.WorkflowId]
        job_id = self._inf_opts[_ExpectedInfParameters.JobId]
        task_id = self._inf_opts[_ExpectedInfParameters.TaskId]

        local_working_dir = self._inf_opts[_ExpectedInfParameters.LocalWorkingDir]
        output_working_dir = pathlib.Path(os.path.join(local_working_dir, workflow_id, job_id, task_id, "outputs"))
        output_working_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        named_output_dir = pathlib.Path(os.path.join(output_working_dir, data.Name))
        named_output_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        remote_working_dir = ""
        named_remote_working_dir = ""
        remote_prefix, found = self.get_injected_envvar(_InjectedEnvVars.RemotePrefix)
        if found:
            remote_working_dir = os.path.join(remote_prefix, workflow_id, job_id, task_id, "outputs")

            named_remote_working_dir = os.path.join(remote_working_dir, data.Name)

        if output_config["type"] == ValueTypes.URL.value or output_config.get(types._IS_ARTIFACT_ATTR_NAME, False):
            value = self._handle_output_asset(
                data.Name,
                ValueTypes.URL,
                str(data.Value),
                str(named_output_dir),
                named_remote_working_dir,
            )
            data.Value = value

        # setting the type
        data.Type = output_config["type"]
        if hasattr(data, "Properties"):
            if "properties" not in output_config and data.Properties is not None:  # type: ignore
                raise ValueError(f"found properties for output `{data.Name}` but config has " "no properties set")
            elif "properties" in output_config and data.Properties is None:  # type: ignore
                data.Properties = types._PropertiesFromConfig(output_config)  # type: ignore

        output = data.model_dump(by_alias=True)

        local_spec_file_path = named_output_dir.joinpath(DATA_SPEC_FILENAME)
        with open(local_spec_file_path, "w+") as f:
            json.dump(output, f)

        if not self._injected_envvars[_InjectedEnvVars.DisableAutoUpload]:
            remote_path = os.path.join(named_remote_working_dir, DATA_SPEC_FILENAME)
            self.logger.info(f"Uploading file: {local_spec_file_path} to {remote_path}")
            self._s3fs.put_file(local_spec_file_path, remote_path)
            self.logger.info("Finished uploading")

        self._output_keys_written.add(data.Name)
        self.update_model_outputs_dict(data.Name, data.Value)
        self.update_outputs_list(output)

    def _flush_output_buffer(self, output_buffer: types.OutputsBuffer) -> None:
        for val in output_buffer:
            self._output_handler(val)

    def success(self) -> Any:
        task_id = self._inf_opts[_ExpectedInfParameters.TaskId]
        success = self._fire_callback(
            types.Callback(
                Id=task_id,
                State=types.ModelStates.COMPLETED,
                Outputs=self.get_outputs_list(),
            )
        )
        # We do it this way so that we can:
        # 1. Fire orchestrator logs only when we're not running locally
        # 2. Still maintain the correct log level
        if not success and self.enable_debug_logs:
            self.logger.error("FAILED: Could not fire Orchestrator callback")

    def failure(
        self,
        exc: Union[Exception, FailedExecutionException],
        data: Optional[Dict[str, Any]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        dexter_clb_url, found = self.get_injected_envvar(_InjectedEnvVars.ClbUrl)
        if not found:
            self.logger.debug("`ORCHESTRATOR_URL` is not set. hence, not firing callback")
            return
        if isinstance(exc, FailedExecutionException):
            err_msg = exc.msg
            failure_type = types.FailureTypes.BADREQUEST.value
        else:
            err_msg = ""
            failure_type = types.FailureTypes.RUNTIME.value

        task_id = self._inf_opts[_ExpectedInfParameters.TaskId]
        end_time = utils.get_current_utc_time_iso()
        self._fire_callback(
            types.Callback(
                Id=task_id,
                State=types.ModelStates.FAILED,
                ErrMsg=err_msg,
                EndTime=end_time,
                FailureType=failure_type,
            )
        )
        raise exc

    def run_model_inference(
        self, *args: Any, **kwargs: Optional[Dict[str, Any]]
    ) -> Tuple[types.OutputsBuffer, Optional[Exception]]:
        inputs: Optional[Dict[str, Any]] = kwargs.get("inputs")
        start_time = utils.get_current_utc_time_iso()
        if inputs is None:
            raise ValueError("inputs cannot be None")

        id = self._inf_opts[_ExpectedInfParameters.TaskId]
        success = self._fire_callback(
            types.Callback(
                Id=id,
                State=types.ModelStates.INPROGRESS,
                Inputs=self.get_inputs_list(),
                StartTime=start_time,
            )
        )
        # We do it this way so that we can:
        # 1. Fire orchestrator logs only when we're not running locally
        # 2. Still maintain the correct log level
        if not success and self.enable_debug_logs:
            self.logger.error("FAILED: Could not fire Orchestrator callback")

        try:
            ctx = asyncio.run_coroutine_threadsafe(self._model.infer(inputs=inputs, opts=None), self._loop).result()
        except Exception as exc:
            self._model.logger.error(exc, exc_info=exc)
            return [], exc
        result = ctx.get_output_buffer()
        self._flush_output_buffer(result)

        serialized_result = types._serialize_output_buffer(result)
        inf_times = ctx.get_model_inf_times()
        end_time = utils.get_current_utc_time_iso()
        clb = types.Callback(
            Id=id,
            State=types.ModelStates.COMPLETED,
            Result=serialized_result,
            EndTime=end_time,
            BlockInfStartTime=inf_times.InfStartTime,
            BlockInfEndTime=inf_times.InfEndTime,
        )
        success = self._fire_callback(clb)
        if not success and self.enable_debug_logs:
            self.logger.error("Failed to fire callback successfully")
        return result, None

    def start(self, **kwargs: Any) -> None:
        """Entrypoint into the runner. Starts the actual process of execution. This involves setting up the model
        runtime, collecting inputs etc.

        Raises:
            ValueError: Raised when arguments are not found but is expected.
            exc: Any other exeception raised by the model.
        """
        self.read_injected_envvars()
        inputs = kwargs.get("args")
        if inputs is None:
            raise ValueError("no inputs found")
        if isinstance(inputs, str):
            inputs = json.loads(inputs)

        # inputs need to be collected here since the taskid is is collected
        # during inputs collection
        rvals = self._collect_inputs(inputs)
        assert rvals is not None
        assert isinstance(rvals, tuple)  # again, statisfying the type checker
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

            task_id = self._inf_opts[_ExpectedInfParameters.TaskId]
            self._fire_callback(
                types.Callback(
                    Id=task_id,
                    State=types.ModelStates.FAILED,
                    ErrMsg="internal server error",
                )
            )
            raise exc
        if self._model.receive_raw_inputs:
            _input_dict = rvals[1]
        else:
            _input_dict = rvals[0]
        self.logger.info("Inputs", _input_dict)
        result, exc = self.run_model_inference(inputs=_input_dict)  # type: ignore
        if exc is not None:
            self.failure(exc=exc)
        self.logger.info(f"Results: {result}")
