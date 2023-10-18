from typing import List, Union

import pydantic
from pydantic import Field
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


FormatPropertyMap = {
    "raster": RasterProperties,
    "vector": VectorProperties,
    "date": DateProperties,
    "tabular": TabularProperties,
}
