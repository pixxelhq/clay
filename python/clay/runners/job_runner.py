import asyncio
import json
import os
import pathlib
import shutil
import time
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from s3fs import S3FileSystem
from urllib3.util import parse_url

from clay import types, utils
from clay.core import DATA_SPEC_FILENAME, BaseRunner, ModelWrapper, ValueTypes
from clay.exceptions import FailedExecutionException, OutputOverwriteException
from clay.logger import Logger, get_streamvalues

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
    RUN_MODE: str = "job"

    def __init__(
        self,
        model_name: str,
        modelcls: ModelWrapper,
        model_args: Dict[str, Any],
        cfg_path: str,
        logger: Optional[Logger] = None,
        enable_uvloop: bool = False,
    ) -> None:
        super().__init__(
            JobRunner.RUN_MODE, modelcls, model_args, cfg_path, logger, enable_uvloop
        )
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

    def set_injected_envvar(
        self, key: _InjectedEnvVars, val: Optional[Union[bool, str]]
    ) -> None:
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

    def get_model_outputs_dict(
        self, key: Optional[str] = None
    ) -> Union[Any, Dict[str, Any]]:
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

    def get_passed_inputs_dict(
        self, key: Optional[str] = None
    ) -> Union[Any, Dict[str, Any]]:
        if key is None:
            return self._passed_inputs_dict
        return self._passed_inputs_dict[key]

    def _handle_input_assets(self, data: types.Data, named_input_dir: str) -> types.Data:
        if not self._injected_envvars[_InjectedEnvVars.AutoDownloadAssets]:
            return data
        if data.Type != ValueTypes.URL.value:
            return data
        url_fragments = parse_url(str(data.Value))
        if url_fragments.scheme != "s3":
            self.logger.warning(
                f"unknown scheme while parsing {data.Value}: {url_fragments.scheme}"
            )
        file_name = os.path.basename(url_fragments.path)  # type: ignore
        local_path = pathlib.Path(named_input_dir, str(file_name))
        self._s3fs.get_file(data.Value, str(local_path))
        if not local_path.exists():
            raise FileNotFoundError(f"failed to find file {data.Value}")
        data.Value = str(local_path)
        return data

    def _backward_compatibility_missing_infparams(self) -> None:
        if self._inf_opts.get(_ExpectedInfParameters.WorkflowId) is None:
            wfid = os.getenv(_ExpectedInfParameters.WorkflowId.value)
            if wfid is None:
                raise ValueError(
                    f"did not find `{_ExpectedInfParameters.WorkflowId.value}`"
                )
            self._inf_opts[_ExpectedInfParameters.WorkflowId] = wfid
        if self._inf_opts.get(_ExpectedInfParameters.JobId) is None:
            jobid = os.getenv(_ExpectedInfParameters.JobId.value)
            if jobid is None:
                raise ValueError(f"did not find `{_ExpectedInfParameters.JobId.value}`")
            self._inf_opts[_ExpectedInfParameters.JobId] = jobid
        if self._inf_opts.get(_ExpectedInfParameters.LocalWorkingDir) is None:
            local_working_dir = os.getenv(_ExpectedInfParameters.LocalWorkingDir.value)
            if local_working_dir is None:
                raise ValueError(
                    f"did not find `{_ExpectedInfParameters.LocalWorkingDir.value}`"
                )
            self._inf_opts[_ExpectedInfParameters.LocalWorkingDir] = local_working_dir
            # The `None` assignment is to statisfy the type checker

    def _collect_inputs(
        self, inputs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Union[Dict[str, Any], Tuple[Dict[str, types.Data], Dict[str, Any]]]]:
        # first we convert list of dicts to a dict of dicts
        if inputs is None:
            raise ValueError("inputs cannot be None")
        tmp = {}
        for i in inputs:
            tmp[i["name"]] = i
        inputs = tmp
        # second we pop the parameters mentioned in `_InfOpts`
        for o in _ExpectedInfParameters:
            val, ke = utils.pop_dict_with_err(inputs, o.value)
            if ke is not None:
                # TODO: make this an fatal error
                self.logger.warning(ke)
            if val is not None:
                self._inf_opts[o] = val.get("value")
                continue
            # self._inf_opts[o] = val
        self._backward_compatibility_missing_infparams()

        workflow_id = self._inf_opts[_ExpectedInfParameters.WorkflowId]
        job_id = self._inf_opts[_ExpectedInfParameters.JobId]
        task_id = self._inf_opts[_ExpectedInfParameters.TaskId]

        local_working_dir = self._inf_opts[_ExpectedInfParameters.LocalWorkingDir]
        input_working_dir = pathlib.Path(
            os.path.join(local_working_dir, workflow_id, job_id, task_id, "inputs")
        )
        input_working_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        _processed_inputs = {}
        for k, v in inputs.items():
            model: types.Data = types._FormatModelMap[v["format"]].model_validate(v)

            named_input_dir = pathlib.Path(input_working_dir, model.Name)
            named_input_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

            model = self._handle_input_assets(model, str(named_input_dir))
            i = model.model_dump(by_alias=True)
            with open(os.path.join(named_input_dir, DATA_SPEC_FILENAME), "w+") as f:
                json.dump(i, f)

            _processed_inputs[k] = model
            self._inputs_prop_map[k] = i["properties"] if "properties" in i else None
            self.update_inputs_list(i)
            self.update_passed_inputs_dict(k, i)
        return _processed_inputs, inputs

    def _handle_output_asset(
        self,
        key: str,
        value_type: ValueTypes,
        src: str,
        named_output_dir: str,
        named_remote_output_dir: str,
    ) -> str:
        if not os.path.exists(src):
            raise FileNotFoundError(f"cannot find src file `{src}`")
        file_name = os.path.basename(src)
        dest = os.path.join(named_output_dir, file_name)
        self.logger.info(f"copying file from `{src}` to `{dest}`")
        _ = shutil.copy(src, dest)
        if named_remote_output_dir != "":
            named_remote_output_dir = os.path.join(named_remote_output_dir, file_name)
            # TODO: Upload to s3 here
            if not self._injected_envvars[_InjectedEnvVars.DisableAutoUpload]:
                self.logger.info(f"uploading file {dest} to {named_remote_output_dir}")
                self._s3fs.put_file(dest, named_remote_output_dir)
                self.logger.info("upload complete")
            return named_remote_output_dir
        return dest

    def _output_handler(self, data: types.Data) -> None:
        if data.Name not in self.expected_outputs:
            self.logger.error(f"`{data.Name}` not found in outputs")
            return

        if data.Name in self._output_keys_written:
            self.logger.error(f"rewritting output key `{data.Name}`")
            raise OutputOverwriteException("attempting to overwrite output")

        output_config = self.expected_outputs[data.Name]
        format = output_config["format"]
        if data.Format != format:
            raise ValueError(f"invalid format `{data.Format}` for `{data.Name}")

        workflow_id = self._inf_opts[_ExpectedInfParameters.WorkflowId]
        job_id = self._inf_opts[_ExpectedInfParameters.JobId]
        task_id = self._inf_opts[_ExpectedInfParameters.TaskId]

        local_working_dir = self._inf_opts[_ExpectedInfParameters.LocalWorkingDir]
        output_working_dir = pathlib.Path(
            os.path.join(local_working_dir, workflow_id, job_id, task_id, "outputs")
        )
        output_working_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        named_output_dir = pathlib.Path(os.path.join(output_working_dir, data.Name))
        named_output_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        remote_working_dir = ""
        named_remote_working_dir = ""
        remote_prefix, found = self.get_injected_envvar(_InjectedEnvVars.RemotePrefix)
        if found:
            remote_working_dir = os.path.join(
                remote_prefix, workflow_id, job_id, task_id, "outputs"
            )

            named_remote_working_dir = os.path.join(remote_working_dir, data.Name)

        if output_config["type"] == ValueTypes.URL.value:
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
            if "properties" not in output_config and data.Properties is not None:
                raise ValueError(
                    f"found properties for output `{data.Name}` but config has "
                    "no properties set"
                )
            elif "properties" in output_config and data.Properties is None:
                data.Properties = types._PropertiesFromConfig(output_config)

        output = data.model_dump(by_alias=True)

        local_spec_file_path = named_output_dir.joinpath(DATA_SPEC_FILENAME)
        with open(local_spec_file_path, "w+") as f:
            json.dump(output, f)

        if not self._injected_envvars[_InjectedEnvVars.DisableAutoUpload]:
            remote_path = os.path.join(named_remote_working_dir, DATA_SPEC_FILENAME)
            self.logger.info(
                f"starting to upload {local_spec_file_path} to {remote_path}"
            )
            self._s3fs.put_file(local_spec_file_path, remote_path)
            self.logger.info("upload complete")

        self._output_keys_written.add(data.Name)
        self.update_model_outputs_dict(data.Name, data.Value)
        self.update_outputs_list(output)

    def _flush_output_buffer(self, output_buffer: types.OutputsBuffer) -> None:
        for val in output_buffer:
            self._output_handler(val)

    def success(self, *args: Any, **kwargs: Any) -> Any:
        task_id = self._inf_opts[_ExpectedInfParameters.TaskId]
        success = self._fire_callback(
            types.Callback(
                Id=task_id,
                State=types.ModelStates.COMPLETED,
                Outputs=self.get_outputs_list(),
                Logs=get_streamvalues(self._logger),
            )
        )
        if not success:
            self.logger.error("failed to fire callback")

    def failure(
        self,
        exc: Union[Exception, FailedExecutionException],
        data: Dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        dexter_clb_url, found = self.get_injected_envvar(_InjectedEnvVars.ClbUrl)
        if not found:
            self.logger.warning("`ORCHESTRATOR_URL` is not set. hence, not firing callback")
            return
        if isinstance(exc, FailedExecutionException):
            err_msg = exc.msg
        else:
            err_msg = ""

        logs = get_streamvalues(self._logger)
        task_id = self._inf_opts[_ExpectedInfParameters.TaskId]
        self._fire_callback(
            types.Callback(
                Id=task_id, State=types.ModelStates.FAILED, ErrMsg=err_msg, Logs=logs
            )
        )
        raise exc

    def run_model_inference(self, inputs: Optional[Dict[str, Any]]) -> Any:
        # inputs: Dict[str, Any] = kwargs.get("inputs")

        if inputs is None:
            raise ValueError("inputs cannot be None")

        id = self._inf_opts[_ExpectedInfParameters.TaskId]
        success = self._fire_callback(
            types.Callback(
                Id=id, State=types.ModelStates.INPROGRESS, Inputs=self.get_inputs_list()
            )
        )
        if not success:
            self.logger.error("Failed to fire callback")

        try:
            result = asyncio.run_coroutine_threadsafe(
                self._model.infer(inputs=inputs, opts=None), self._loop
            ).result()
        except Exception as exc:
            self._model.logger.error(exc, exc_info=exc)
            return [], exc

        self._flush_output_buffer(result)
        return result, None

    def start(self, **kwargs: Any) -> None:
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
        _std_input_dict = rvals[1]
        try:
            self._init_model()
            self._init_model_inference_event_loop()
        except Exception as exc:
            self._logger.error(exc)
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            time.sleep(2)
            self._logger.debug(f"Event loop running status: {self._loop.is_running()}")
            self._logger.debug(f"thread alive status: {self._t.is_alive()}")

            task_id = self._inf_opts[_ExpectedInfParameters.TaskId]
            self._fire_callback(
                types.Callback(
                    Id=task_id,
                    State=types.ModelStates.FAILED,
                    ErrMsg="internal server error",
                    Logs=get_streamvalues(self._logger),
                )
            )
        result, exc = self.run_model_inference(inputs=_std_input_dict)  # type: ignore
        if exc is not None:
            self.failure(exc)
        self.logger.info(f"results: {result}")
