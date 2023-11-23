from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

import pydantic
from pydantic import ConfigDict, Field
from typing_extensions import Annotated

PARAMETER_ATTR_NAME = "parameter"
PERSISTENT_ATTR_NAME = "persistent"
_IS_ARTIFACT_ATTR_NAME = "is_artifact"


class InferenceStates(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    FAILED = "failed"
    SUCCESS = "success"


class ModelStates(str, Enum):
    STARTED = "TaskStarted"
    INPROGRESS = "TaskInprogress"
    COMPLETED = "TaskCompleted"
    FAILED = "TaskFailed"

    def __repr__(self) -> str:
        return self.value


class PrimitiveTypes(Enum):
    URL = "url"
    STR = "str"
    INT = "int"
    FLOAT = "float"


class FormatTypes(Enum):
    RASTER = "raster"
    VECTOR = "vector"
    DATE = "date"
    STRING = "string"
    NUMBER = "number"
    TABULAR = "tabular"


def add_inline_fields(
    from_model: Type[pydantic.BaseModel], to_model: Type[pydantic.BaseModel]
) -> None:
    for k, v in from_model.__annotations__.items():
        to_model.__annotations__[k] = v


class RasterProperties(pydantic.BaseModel):
    Bands: Annotated[
        Optional[List[str]], Field(serialization_alias="bands", alias="bands")
    ] = None
    Source: Annotated[
        Optional[str], Field(serialization_alias="source", alias="source")
    ] = None
    Collection: Annotated[
        Optional[str], Field(serialization_alias="collection", alias="collection")
    ] = None
    Dtype: Annotated[
        Optional[str], Field(serialization_alias="dtype", alias="dtype")
    ] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class VectorProperties(pydantic.BaseModel):
    Geometry: Annotated[Optional[str], Field(serialization_alias="geometry")] = None


class DateProperties(pydantic.BaseModel):
    FromAoi: Annotated[Optional[bool], Field(serialization_alias="from_aoi")] = None


class TabularFileSchema(pydantic.BaseModel):
    Headers: Annotated[Optional[List[str]], Field(serialization_alias="headers")] = None


class TabularProperties(pydantic.BaseModel):
    FileType: Annotated[Optional[str], Field(serialization_alias="file_type")] = None
    FileSchema: Annotated[
        Optional[TabularFileSchema], Field(serialization_alias="file_schema")
    ] = None


Properties = Union[RasterProperties, VectorProperties, DateProperties, TabularProperties]


FormatPropertyMap = {
    FormatTypes.RASTER.value: RasterProperties,
    FormatTypes.VECTOR.value: VectorProperties,
    FormatTypes.DATE.value: DateProperties,
    FormatTypes.TABULAR.value: TabularProperties,
}


def _PropertiesFromConfig(output_cfg: Dict[str, Any]) -> Optional[Properties]:
    format = output_cfg["format"]
    props = output_cfg.get("properties")
    if props is None:
        return None
    return FormatPropertyMap[format].model_validate(props)


class Callback(pydantic.BaseModel):
    Id: Annotated[str, Field(serialization_alias="id")]
    State: Annotated[
        ModelStates, Field(serialization_alias="state")
    ] = ModelStates.INPROGRESS
    Inputs: Annotated[
        Optional[List[Dict[str, Any]]], Field(serialization_alias="inputs")
    ] = None
    Outputs: Annotated[
        Optional[List[Dict[str, Any]]], Field(serialization_alias="outputs")
    ] = None
    Logs: Annotated[Optional[str], Field(serialization_alias="logs")] = ""
    UserLogs: Annotated[Optional[str], Field(serialization_alias="user_logs")] = ""
    ErrMsg: Annotated[Optional[str], Field(serialization_alias="err_msg")] = ""

    model_config = ConfigDict(use_enum_values=False)


class InferenceOpts(pydantic.BaseModel):
    Id: str
    InputList: List[Dict[str, Any]] = []
    InputPropMap: Dict[str, Any] = defaultdict(None)


class _DataMeta(pydantic.BaseModel):
    Format: Annotated[str, Field(alias="format", serialization_alias="format")]
    Type: Annotated[Optional[str], Field(alias="type", serialization_alias="type")] = None
    Name: Annotated[str, Field(alias="name", serialization_alias="name")]
    Value: Annotated[
        Optional[Union[int, float, str, bool]],
        Field(alias="value", serialization_alias="value"),
    ] = None
    Default: Annotated[
        Optional[Union[int, float, str, bool]],
        Field(alias="default", serialization_alias="default"),
    ] = None
    IsArtifact: Annotated[
        Optional[bool], Field(alias="is_artifact", serialization_alias="is_artifact")
    ] = None

    model_config = {"validate_assignment": True, "populate_by_name": True}


class Raster(_DataMeta):
    Properties: Annotated[
        Optional[RasterProperties],
        Field(serialization_alias="properties", alias="properties"),
    ] = None

    model_config = {"validate_assignment": True, "populate_by_name": True}

    def __init__(
        __pydantic_self__,
        name: str,
        value: Union[int, float, str, bool],
        default: Optional[Union[str, int, float, bool]] = None,
        is_artifact: Optional[bool] = True,
        properties: Optional[RasterProperties] = None,
        *args: Any,
        **kwargs: Any,
    ):
        # `Type` is set as best guess here. This would anyway be overriden based on
        # the output config
        super().__init__(
            Format=FormatTypes.RASTER.value,
            Name=name,
            Value=value,
            Type=PrimitiveTypes.URL.value,
            Default=default,
            IsArtifact=is_artifact,
        )
        __pydantic_self__.Properties = properties


class Vector(_DataMeta):
    Properties: Annotated[
        Optional[VectorProperties],
        Field(serialization_alias="properties", alias="properties"),
    ] = None

    model_config = {"validate_assignment": True, "populate_by_name": True}

    def __init__(
        __pydantic_self__,
        name: str,
        value: str,
        default: Optional[Union[str, int, float, bool]] = None,
        is_artifact: Optional[bool] = True,
        properties: Optional[VectorProperties] = None,
    ):
        super().__init__(
            Format=FormatTypes.VECTOR.value,
            Type=PrimitiveTypes.URL.value,
            Name=name,
            Value=value,
            IsArtifact=is_artifact,
            Default=default,
        )
        __pydantic_self__.Properties = properties


class Date(_DataMeta):
    Properties: Annotated[
        Optional[DateProperties],
        Field(serialization_alias="properties", alias="properties"),
    ] = None

    model_config = {"validate_assignment": True, "populate_by_name": True}

    def __init__(
        __pydantic_self__,
        name: str,
        value: str,
        properties: Optional[DateProperties] = None,
        default: Optional[Union[str, int, float, bool]] = None,
    ):
        super().__init__(
            Format=FormatTypes.DATE.value,
            Type=PrimitiveTypes.STR.value,
            Name=name,
            Value=value,
            IsArtifact=False,
            Default=default,
        )
        __pydantic_self__.Properties = properties


class Tabular(_DataMeta):
    Properties: Annotated[
        Optional[TabularProperties],
        Field(serialization_alias="properties", alias="properties"),
    ] = None

    model_config = {"validate_assignment": True, "populate_by_name": True}

    def __init__(
        __pydantic_self__,
        name: str,
        value: str,
        is_artifact: Optional[bool] = True,
        properties: Optional[TabularProperties] = None,
        default: Optional[Union[str, int, float, bool]] = None,
    ):
        super().__init__(
            Format=FormatTypes.TABULAR.value,
            Value=value,
            Name=name,
            Type=PrimitiveTypes.URL.value,
            IsArtifact=is_artifact,
            Default=default,
        )
        __pydantic_self__.Properties = properties


class String(_DataMeta):
    # pydantic throws error without this
    __null__: Any

    def __init__(
        __pydantic_self__,
        name: str,
        value: Optional[str] = None,
        default: Optional[Union[str, int, float, bool]] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(
            Format=FormatTypes.STRING.value,
            Name=name,
            Type=PrimitiveTypes.STR.value,
            Value=value,
            IsArtifact=False,
            Default=default,
        )


class Number(_DataMeta):
    # pydantic throws error without this
    __null__: Any

    def __init__(
        __pydantic_self__,
        name: str,
        value: Union[int, float, None] = None,
        default: Optional[Union[str, int, float, bool]] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(
            Format=FormatTypes.NUMBER.value,
            Name=name,
            Type=PrimitiveTypes.FLOAT.value,
            Value=value,
            IsArtifact=False,
            Default=default,
        )


# add_inline_fields(DataMeta, Number)

Data = Union[Raster, Vector, Date, Tabular, String, Number]

_FormatModelMap = {
    FormatTypes.RASTER.value: Raster,
    FormatTypes.VECTOR.value: Vector,
    FormatTypes.DATE.value: Date,
    FormatTypes.NUMBER.value: Number,
    FormatTypes.STRING.value: String,
    FormatTypes.TABULAR.value: Tabular,
}

OutputsBuffer = List[Data]
