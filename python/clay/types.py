from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

import pydantic
from pydantic import ConfigDict, Field
from typing_extensions import Annotated


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
    print("xxx")
    for k, v in from_model.__annotations__.items():
        to_model.__annotations__[k] = v
    print("yyy")


class RasterProperties(pydantic.BaseModel):
    Bands: Annotated[List[str], Field(serialization_alias="bands")]
    Source: Annotated[str, Field(serialization_alias="source")]
    Collection: Annotated[str, Field(serialization_alias="collection")]
    Dtype: Annotated[str, Field(serialization_alias="dtype")]


class VectorProperties(pydantic.BaseModel):
    Geometry: Annotated[str, Field(serialization_alias="geometry")]


class DateProperties(pydantic.BaseModel):
    FromAoi: Annotated[bool, Field(serialization_alias="from_aoi")]


class TabularFileSchema(pydantic.BaseModel):
    Headers: Annotated[List[str], Field(serialization_alias="headers")]


class TabularProperties(pydantic.BaseModel):
    FileType: Annotated[str, Field(serialization_alias="file_type")]
    FileSchema: Annotated[TabularFileSchema, Field(serialization_alias="file_schema")]


Properties = Union[RasterProperties, VectorProperties, DateProperties, TabularProperties]


FormatPropertyMap = {
    FormatTypes.RASTER.value: RasterProperties,
    FormatTypes.VECTOR.value: VectorProperties,
    FormatTypes.DATE.value: DateProperties,
    FormatTypes.TABULAR.value: TabularProperties,
}


def _PropertiesFromConfig(output_cfg: Dict[str, Any]) -> Properties:
    format = output_cfg["format"]
    return FormatPropertyMap[format].model_validate(output_cfg["properties"])


class DataMeta(pydantic.BaseModel):
    Format: Annotated[str, Field(serialization_alias="format")]
    Type: Annotated[str, Field(serialization_alias="type")]
    Name: Annotated[str, Field(serialization_alias="name")]
    Value: Annotated[
        Union[int, float, str, str, bool], Field(serialization_alias="value")
    ]


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


class _DataMetaBase(pydantic.BaseModel):
    Format: Annotated[str, Field(serialization_alias="format")]
    Type: Annotated[Optional[str], Field(serialization_alias="type")] = None
    Name: Annotated[str, Field(serialization_alias="name")]
    Value: Annotated[
        Optional[Union[int, float, str, str, bool]], Field(serialization_alias="value")
    ] = None

    model_config = {"validate_assignment": True}


class Raster(_DataMetaBase):
    Properties: Annotated[
        Optional[RasterProperties], Field(serialization_alias="properties")
    ] = None

    model_config = {"validate_assignment": True}

    def __init__(
        __pydantic_self__,
        name: str,
        value: Union[int, float, str, bool],
        properties: Optional[RasterProperties] = None,
        *args: Any,
        **kwargs: Any,
    ):
        # `Type` is set as best guess here. This would anyway be overriden based on
        # the output config
        super().__init__(
            Format="raster", Name=name, Value=value, Type=PrimitiveTypes.URL.value
        )
        __pydantic_self__.Properties = properties


class Vector(_DataMetaBase):
    Properties: Annotated[
        Optional[VectorProperties], Field(serialization_alias="properties")
    ] = None

    model_config = {"validate_assignment": True}

    def __init__(
        __pydantic_self__,
        name: str,
        value: str,
        properties: Optional[VectorProperties] = None,
    ):
        super().__init__(
            Format="vector", Type=PrimitiveTypes.URL.value, Name=name, Value=value
        )
        __pydantic_self__.Properties = properties


class Date(_DataMetaBase):
    Properties: Annotated[
        Optional[DateProperties], Field(serialization_alias="properties")
    ] = None

    model_config = {"validate_assignment": True}

    def __init__(
        __pydantic_self__,
        name: str,
        value: str,
        properties: Optional[DateProperties] = None,
    ):
        super().__init__(
            Format="date", Type=PrimitiveTypes.STR.value, Name=name, Value=value
        )
        __pydantic_self__.Properties = properties


class Tabular(_DataMetaBase):
    Properties: Annotated[
        Optional[TabularProperties], Field(serialization_alias="properties")
    ] = None

    model_config = {"validate_assignment": True}

    def __init__(
        __pydantic_self__,
        name: str,
        value: str,
        properties: Optional[TabularProperties] = None,
    ):
        super().__init__(
            Format="tabular", Value=value, Name=name, Type=PrimitiveTypes.URL.value
        )
        __pydantic_self__.Properties = properties


class String(_DataMetaBase):
    # pydantic throws error without this
    __null__: Any

    def __init__(__pydantic_self__, name: str, value: str, *args: Any, **kwargs: Any):
        super().__init__(
            Format="string", Name=name, Type=PrimitiveTypes.STR.value, Value=value
        )


class Number(_DataMetaBase):
    # pydantic throws error without this
    __null__: Any

    def __init__(
        __pydantic_self__,
        name: str,
        value: Union[int, float],
    ):
        super().__init__(
            Format="number", Name=name, Type=PrimitiveTypes.FLOAT.value, Value=value
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
