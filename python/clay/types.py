from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import pydantic
from pydantic import ConfigDict, Field
from typing_extensions import Annotated


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


class DataMeta(pydantic.BaseModel):
    Format: Annotated[str, Field(serialization_alias="format")]
    Type: Annotated[str, Field(serialization_alias="type")]
    Name: Annotated[str, Field(serialization_alias="name")]
    Value: Annotated[
        Union[int, float, str, str, bool], Field(serialization_alias="value")
    ]


class PrimitiveType(pydantic.BaseModel):
    pass


class URL(PrimitiveType):
    value: str


class Str(PrimitiveType):
    value: str


class Int(PrimitiveType):
    value: int


class Float(PrimitiveType):
    value: float


class ModelStates(Enum):
    STARTED = "TaskStarted"
    INPROGRESS = "TaskInprogress"
    COMPLETED = "TaskCompleted"
    FAILED = "TaskFailed"


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

    model_config = ConfigDict(use_enum_values=True)


class InferenceOpts(pydantic.BaseModel):
    Id: str
    InputList: List[Dict[str, Any]] = []
    InputPropMap: Dict[str, Any] = defaultdict(None)


OutputsBuffer = List[
    Tuple[
        str,
        Union[str, int, float],
        Optional[
            Union[
                RasterProperties,
                VectorProperties,
                DateProperties,
                TabularProperties,
                Dict[str, Any],
            ]
        ],
    ],
]

FormatPropertyMap = {
    "raster": RasterProperties,
    "vector": VectorProperties,
    "date": DateProperties,
    "tabular": TabularProperties,
}
