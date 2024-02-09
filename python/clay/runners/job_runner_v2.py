import asyncio
import json
import os
import pathlib
import shutil
import time
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import clay
from clay import types
from clay.core import DATA_SPEC_FILENAME, BaseRunner, ModelWrapper, ValueTypes
from clay.exceptions import FailedExecutionException, OutputOverwriteException
from clay.logger import Logger, get_streamvalues
from clay.utils import (
    cast_inputs,
    convert_list_to_dict,
    get_current_utc_time_iso,
    get_filename_from_remote,
    get_io_dirmap,
)


class _InjectedEnvVars(Enum):
    TaskId = "TASK_ID"
    TaskName = "TASK_NAME"
    WorkingDir = "WORKING_DIR"
    InputsWorkingDir = "INPUTS_WORKING_DIR"
    OutputsWorkingDir = "OUTPUTS_WORKING_DIR"
    OutputsRemotePath = "OUTPUTS_REMOTE_PATH"
    Env = "ENV"


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
    RUN_MODE: str = "argo"

    def __init__(
        self,
        model_name: str,
        modelcls: ModelWrapper,
        model_args: Dict[str, Any],
        cfg_path: str,
        logger: Union[Logger, None] = None,
        enable_uvloop: bool = False,
    ) -> None:
        super().__init__(
            JobRunnerV2.RUN_MODE, modelcls, model_args, cfg_path, logger, enable_uvloop
        )
        self.model_name = model_name
        self._injected_envvars: Dict[_InjectedEnvVars, str] = {}
        self._inputs_prop_map: Dict[str, Any] = defaultdict(None)
        self._inputs_list: List[Dict[str, Any]] = []
        self._passed_inputs_dict: Dict[str, Any] = {}
        self._outputs_list: List[Dict[str, Any]] = []

        self.expected_outputs = dict((oi["name"], oi) for oi in self.config.outputs)
        self._model_outputs_dict: Dict[str, Any] = {}
        self._output_keys_written: Set[str] = set()

        # Dict rep of https://argoproj.github.io/argo-workflows/fields/#template
        self._argo_template_spec: Dict[str, Any] = {}

        # self._manual_s3_sync_list: List[Tuple[]]

    def get_injected_envvar(self, key: _InjectedEnvVars) -> Tuple[str, bool]:
        val = self._injected_envvars.get(key)
        if val is None:
            return "", False
        return val, True

    def set_injected_envvar(self, key: _InjectedEnvVars, val: str) -> None:
        self._injected_envvars[key] = val

    def read_injected_envvars(self) -> None:
        for e in _InjectedEnvVars:
            val = os.getenv(e.value)
            if val is None:
                if e in REQUIRED_ENVVAR:
                    self.logger.error(f"required env-var `{e.name}` not found")
                    clay.failure("missing required configuration")
                self.logger.warn(f"env-var `{e.name}` not found")
                continue
            self.set_injected_envvar(e, val)

        # additionally reading argo related env fields
        self._read_argo_template_spec()

    def set_inputs_propmap(self, key: str, value: Dict[Any, Any]) -> None:
        self._inputs_prop_map[key] = value

    def get_inputs_propmap(
        self, key: Union[str, None]
    ) -> Union[Dict[Any, Any], Dict[str, Any]]:
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

    def get_passed_inputs_dict(
        self, key: Optional[str] = None
    ) -> Union[Any, Dict[str, Any]]:
        if key is None:
            return self._passed_inputs_dict
        return self._passed_inputs_dict[key]

    def update_model_outputs_dict(self, key: str, value: Any) -> None:
        self._model_outputs_dict[key] = value

    def get_model_outputs_dict(
        self, key: Optional[str] = None
    ) -> Union[Any, Dict[str, Any]]:
        if key is None:
            return self._model_outputs_dict
        return self._model_outputs_dict[key]

    def _read_argo_template_spec(self) -> None:
        s = os.getenv(_ArgoConfEnvVars.ArgoTemplate.value)
        if s is None:
            self.logger.warning(
                f"could not read {_ArgoConfEnvVars.ArgoTemplate.value} from env"
            )
            return
        self._argo_template_spec = json.loads(s)

    def _handle_parameter_input(
        self, name: str, value: Any, input_cfg: Dict[str, Any]
    ) -> Any:
        model: types.Data = types._FormatModelMap[input_cfg["format"]].model_validate(
            input_cfg
        )
        model.Value = value
        # wtf to do here?

    def _handle_artifact_input(self, name: str, value: Any, value_type: Any) -> Any:
        pass

    # The `None` assignment is to statisfy the type checker
    def _collect_inputs(
        self, inputs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Union[Dict[str, Any], Tuple[Dict[str, types.Data], Dict[str, Any]]]]:
        # NOTE: we have removed default fills for inputs that the model expects and have
        # not been provided. it is expected that this would be handled at the executor
        # level. In-case, an input is received that is nor provided we fail the model

        # get list of input parameters from argo template
        if "parameters" in self._argo_template_spec.get("inputs", {}):
            _input_parameters = convert_list_to_dict(
                self._argo_template_spec["inputs"].get("parameters"), "name"
            )

        input_dict: Dict[str, Any] = {}
        processed_inputs: Dict[str, types.Data] = {}
        input_working_dir, found = self.get_injected_envvar(
            _InjectedEnvVars.InputsWorkingDir
        )
        input_dirmap = get_io_dirmap(self.config.inputs, input_working_dir)
        for i in self.config.inputs:
            # check if the input i is a parameter or not. By default, we assume it to
            # be a parameter
            if i.get(types._IS_ARTIFACT_ATTR_NAME, False):
                path = input_dirmap.get(i["name"])

                if path is None:
                    # fail the model if input is not found
                    clay.failure(f"`{i['name']}` not found")

                with open(os.path.join(path, DATA_SPEC_FILENAME)) as f:  # type: ignore
                    spec = json.load(f)

                # here we store the list of inputs as read from the json
                self.update_inputs_list(spec.copy())

                value_type = spec["type"]
                value = cast_inputs(spec["value"], value_type)

                # CRITICAL: At this point in the function we do two things,
                # 1. If type is `url`, clay expects an asset file to be present in `path`.
                # Please note, that
                # clay expects that the filename of the asset would be the filename
                #  specified
                # by the url in the `value` parameter.
                # 2. We take the filename, check if the file actually exists or not.
                # If it does, we pass the local path to the relevant input parameter.
                # If it does not, we fail the model.
                if value_type == ValueTypes.URL.value:
                    filename = get_filename_from_remote(value)
                    # we convert the remote url to the local path of the asset
                    value = os.path.join(path, filename)  # type: ignore

                spec["value"] = value
                data: types.Data = types._FormatModelMap[i["format"]].model_validate(spec)
                input_dict[i["name"]] = spec
                processed_inputs[i["name"]] = data

                self.set_inputs_propmap(i["name"], spec)

                # here we update the dict storing the actual values that are passed to
                # the model functions, post any cleanups
                self.update_passed_inputs_dict(i["name"], value)
            else:
                # if it is is not persistent parameter then for sure the data item is a
                # parameter
                value = _input_parameters[i["name"]].get("value", None)
                if value is None:
                    value = i.get("value")
                value_type = i["type"]
                value = cast_inputs(value, value_type)
                i["value"] = value
                data: types.Data = types._FormatModelMap[i["format"]].model_validate(i)  # type: ignore # noqa

                # now we manually create a json representation of this data item since
                # this is a parameter
                data_dict = data.model_dump(by_alias=True)

                # TODO: remove this and make it more efficient. ideally path ops should be
                # dealt in the caller of _collect_inputs.
                spec_path = pathlib.Path(os.path.join(input_working_dir, i["name"]))
                spec_path.mkdir(exist_ok=True, parents=True)
                with open(os.path.join(spec_path, DATA_SPEC_FILENAME), "w+") as f:
                    json.dump(data_dict, f)
                input_dict[i["name"]] = i
                processed_inputs[i["name"]] = data
                self.set_inputs_propmap(i["name"], data_dict)
                self.update_inputs_list(data_dict)
                self.update_passed_inputs_dict(i["name"], value)

        return processed_inputs, input_dict

    def _handle_output_asset(
        self, key: str, value_type: ValueTypes, src: str, named_output_dir: str
    ) -> str:
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
        print("handle output asset ", key, value_type, src, named_output_dir)
        # replaces any preexisting files
        if not os.path.exists(src):
            raise FileNotFoundError(f"cannot find src file `{src}`")
        file_name = os.path.basename(src)
        _ = shutil.copy(src, os.path.join(named_output_dir, file_name))
        assert os.path.exists(os.path.join(named_output_dir, file_name))
        remote_path, found = self.get_injected_envvar(_InjectedEnvVars.OutputsRemotePath)
        remote_path = os.path.join(remote_path, key, file_name)
        return remote_path

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
            self.logger.error(f"`{data.Name}` not found in outputs config")
            return

        if data.Name in self._output_keys_written:
            self.logger.error(f"rewritting output key `{data.Name}`")
            raise OutputOverwriteException("attempting key overwrite")

        output_config = self.expected_outputs[data.Name]
        format = output_config["format"]
        if data.Format != format:
            raise ValueError(
                f"invalid format `{data.Format}` for `{data.Name}`. Expected `{format}`"
            )

        output_working_dir, found = self.get_injected_envvar(
            _InjectedEnvVars.OutputsWorkingDir
        )
        named_output_dir = pathlib.Path(os.path.join(output_working_dir, data.Name))
        named_output_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
        print(os.listdir(output_working_dir))
        assert os.path.exists(named_output_dir)
        print("named output dir ", named_output_dir)
        print("data: ", data)

        # here we check if the output item in question is an artifact or not. If it
        # is not, then we dont process any supporting artifact file.
        if output_config["type"] == ValueTypes.URL.value or output_config.get(
            types._IS_ARTIFACT_ATTR_NAME, False
        ):
            value = self._handle_output_asset(
                data.Name, ValueTypes.URL, str(data.Value), str(named_output_dir)
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

        output_parameter_path = pathlib.Path(os.path.join(output_working_dir, data.Name))
        output_parameter_path.mkdir(mode=0o777, parents=True, exist_ok=True)

        self._output_keys_written.add(data.Name)
        self.update_model_outputs_dict(data.Name, data.Value)
        self.update_outputs_list(output)

        with open(output_parameter_path.joinpath(DATA_SPEC_FILENAME), "w+") as f:
            json.dump(output, f)

    def _flush_output_buffer(self, output_buffer: types.OutputsBuffer) -> None:
        for val in output_buffer:
            self._output_handler(val)

    def success(self) -> None:
        task_id, found = self.get_injected_envvar(_InjectedEnvVars.TaskId)
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
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if self._dexter_clb_url is None:
            self._logger.warning("`ORCHESTRATOR_URL` is not set, hence not firing callback")
            return
        if isinstance(exc, FailedExecutionException):
            err_msg = exc.msg
        else:
            err_msg = ""

        logs = get_streamvalues(self._logger)
        task_id, _ = self.get_injected_envvar(_InjectedEnvVars.TaskId)
        end_time = get_current_utc_time_iso()
        self._fire_callback(
            types.Callback(
                Id=task_id,
                State=types.ModelStates.FAILED,
                ErrMsg=err_msg,
                Logs=logs,
                EndTime=end_time,
            )
        )
        self._logger.info("inference finished")
        raise exc

    def run_model_inference(self) -> Tuple[types.OutputsBuffer, Optional[Exception]]:
        start_time = get_current_utc_time_iso()

        rvals = self._collect_inputs()
        assert rvals is not None
        print(rvals)
        if self._model.receive_raw_inputs:
            input_dict = rvals[1]  # type: ignore
        else:
            input_dict = rvals[0]  # type: ignore
        assert isinstance(input_dict, dict)
        id, _ = self.get_injected_envvar(_InjectedEnvVars.TaskId)

        # fire inprogress callback
        success = self._fire_callback(
            types.Callback(
                Id=id,
                State=types.ModelStates.INPROGRESS,
                Inputs=self.get_inputs_list(),
                StartTime=start_time,
            )
        )
        if not success:
            self.logger.error("failed to fire callback")

        opts = types.InferenceOpts(
            Id=id,
            InputList=self.get_inputs_list(),
            InputPropMap=self.get_inputs_propmap(None),
        )
        print(input_dict)
        try:
            ctx = asyncio.run_coroutine_threadsafe(
                self._model.infer(inputs=input_dict, opts=opts),
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
        )
        success = self._fire_callback(clb)
        if not success:
            self.logger.warn("could not successfully fire callback")
        return result, None

    def start(self, **kwargs: Any) -> None:
        self.read_injected_envvars()
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

            task_id, _ = self.get_injected_envvar(_InjectedEnvVars.TaskId)
            self._fire_callback(
                types.Callback(
                    Id=task_id,
                    State=types.ModelStates.FAILED,
                    ErrMsg="internal server error",
                    Logs=get_streamvalues(self._logger),
                )
            )

        result, exc = self.run_model_inference()  # type: ignore
        if exc is not None:
            self.failure(exc)
        self._logger.info(f"results: {result}")
