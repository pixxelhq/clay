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
EXECUTOR_ENVVAR = "EXECUTOR"


class _CommonEnvvars(str, Enum):
    ORCHESTRATOR_URL = "ORCHESTRATOR_URL"
    DEXTER_RUN_TYPE = "DEXTER_RUN_TYPE"
    DEXTER_HOST = "DEXTER_HOST"
    DEXTER_PORT = "DEXTER_PORT"
    TASK_ID = "task_id"


class FailureTypes(str, Enum):
    RUNTIME = "runtime_exception"
    BADREQUEST = "bad_request"


class ModelStates(str, Enum):
    STARTED = "created"
    INPROGRESS = "inprogress"
    COMPLETED = "completed"
    FAILED = "failed"

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


def add_inline_fields(from_model: Type[pydantic.BaseModel], to_model: Type[pydantic.BaseModel]) -> None:
    for k, v in from_model.__annotations__.items():
        to_model.__annotations__[k] = v


class DiscretizationItem(pydantic.BaseModel):
    """Identifies each class in the _discretized_ distribution. In the case of an `interval` based discretization,
    we specify the `Range` attribute, denoting the range of the pixel values which fall under a particular class.
    In the case of an `index` based discretization, we specify the `Value` attribute, denoting the index value which
    represents the class. The `Range` and `Value` attributes are mutually-exclusive.

    Args:
        Color (Optional[str]): Color of the class. Represented in [Hex Code](https://www.color-hex.com/).
        Name (Optional[str]): Name of the class.
        Value (Optional[str]): Index value representing the class, in the case of `index`-based discretization.
        Range (Optional[List[float]]): List representing the `min` and `max` for a given range, that represents
            a class, given that the type of discretization is `interval`.
    """

    Color: Annotated[Optional[str], Field(serialization_alias="color", alias="color")] = None
    Name: Annotated[Optional[str], Field(serialization_alias="name", alias="name")] = None
    Value: Annotated[Optional[str], Field(serialization_alias="value", alias="value")] = None
    Range: Annotated[Optional[List[float]], Field(serialization_alias="range", alias="range")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class RasterDiscretization(pydantic.BaseModel):
    """Supports discretization of the underlying pixel distribution. This is to be used when we want to
    convey one of two things,

    1. Represent a continuous distribution as discrete intervals.

    2. Represent information regarding the underlying discrete distribution.

    Args:
        Type (Optional[str]): Type of discretization done. Values are `interval` or `index`.
        Classes (Optional[List[DiscretizationItem]]): Information regarding each class in the resultant discrete dist.
    """

    Type: Annotated[Optional[str], Field(serialization_alias="type", alias="type")] = None
    Classes: Annotated[
        Optional[List[DiscretizationItem]],
        Field(serialization_alias="classes", alias="classes"),
    ] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class VizContinuous(pydantic.BaseModel):
    """Supported visualisation for continuous values.

    Attributes:
        ColorMapName (Annotated[Optional[str]]): Colormap to be used for the continous visualisation. Supported
            colormaps can be found [here](https://cogeotiff.github.io/rio-tiler/colormap/#default-rio-tilers-colormaps).
        Range (Annotated[Optional[List[List[float]]]]): Bandwise range of the pixel values in the format [min, max].
    """

    ColorMapName: Annotated[Optional[str], Field(serialization_alias="name", alias="name")] = None
    Range: Annotated[Optional[List[List[float]]], Field(serialization_alias="range", alias="range")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class VizBucket(pydantic.BaseModel):
    """Supported visualisation for histograms.

    Attributes:
        Range (Annotated[Optional[List[float]]]): Range of the pixel values in the format [min, max].
        ColorCode (Annotated[Optional[str]]): Hex code of the color.
    """

    Range: Annotated[Optional[List[float]], Field(serialization_alias="range", alias="range")] = None
    ColorCode: Annotated[Optional[str], Field(serialization_alias="color", alias="color")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class RasterVisualisation(pydantic.BaseModel):
    """Supported visualisation options for a raster.

    Attributes:
        Type (str): Type of the visualisation. The supported values are [continuous, bucket, discrete].
        Continuous (Annotated[Optional[List[VizContinuous]]]): Defines the options for _continuous_ visualisation.
        Bucket (Annotated[Optional[List[List[VizBucket]]]]): Defines the options for _histogram_ based visualisatin.
        Discrete (Annotated[Optional[Dict[str, str]]]): Defines the pixel class value and color mapping.
    """

    Type: Annotated[Optional[str], Field(serialization_alias="type", alias="type")] = None
    Continuous: Annotated[
        Optional[VizContinuous],
        Field(serialization_alias="continuous", alias="continuous"),
    ] = None
    Bucket: Annotated[
        Optional[List[List[VizBucket]]],
        Field(serialization_alias="bucket", alias="bucket"),
    ] = None
    Discrete: Annotated[
        Optional[Dict[str, str]],
        Field(serialization_alias="discrete", alias="discrete"),
    ] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class RasterProperties(pydantic.BaseModel):
    """Supported properties for a raster

    Attributes:
        Bands:
            List of bands that the raster contains. This list is expected to be *ordered*, meaning
            that the order of bands in the raster should corresspond with the order of bands in this
            list. Defaults to `None`.
        Source:
            The orignal provider of the tiles. While this is a string and can really contain any values,
            we generally support `planetary` and `pixxel`. Defaults to `None`.
        Collection:
            The satellite collection. Defaults to `None`.
        Dtype:
            The type of literal values in the raster. Defaults to `None`.
        Date:
            The date of the Raster
        Images:
            The STAC URLs of the images used to create the raster.
        SunElevation:
            Sun Elevation angle of the raster
        SatelliteLookAngle:
            Satellite Look angle of the raster.
        Visualisation:
            It will help in the raster visualisation on client side. There are three type of visualisation supported.

            1. Continuous:
                Mentions the colormap gradient with a range of distribution values. We support colormaps from this [list](https://cogeotiff.github.io/rio-tiler/colormap/#default-rio-tilers-colormaps).
                Supports multibands wherein the index of this list corressponds to the index of the band in the raster file to which this viz is intended
                for.

            2. Discrete:
                Defines a mapping between pixel class values and corresponding color code. Each class would be given the
                color code specified in their corressponding key. Discrete viz is intended only for single-band rasters.

            3. Bucket:
                Defines a histogram based visualisation technique for pixel values. Supports multibands wherein the index
                of this list corressponds to the index of the band in the raster file to which this viz is intended for.
        Discretization:
           This helps in one of two things,

            1. Discretizing an continuous distribution.

            2. Passing along metadata for an already discrete interval.

    """

    Bands: Annotated[Optional[List[str]], Field(serialization_alias="bands", alias="bands")] = None
    Source: Annotated[Optional[str], Field(serialization_alias="source", alias="source")] = None
    Collection: Annotated[Optional[str], Field(serialization_alias="collection", alias="collection")] = None
    Dtype: Annotated[Optional[str], Field(serialization_alias="dtype", alias="dtype")] = None
    SunElevation: Annotated[
        Optional[float],
        Field(serialization_alias="sun_elevation", alias="sun_elevation"),
    ] = None
    SatelliteLookAngle: Annotated[
        Optional[float],
        Field(serialization_alias="satellite_look_angle", alias="satellite_look_angle"),
    ] = None
    Visualisation: Annotated[
        Optional[RasterVisualisation],
        Field(serialization_alias="visualisation", alias="visualisation"),
    ] = None
    Date: Annotated[Optional[str], Field(serialization_alias="date", alias="date")] = None
    Discretization: Annotated[
        Optional[RasterDiscretization],
        Field(serialization_alias="discretization", alias="discretization"),
    ] = None
    Images: Annotated[Optional[List[str]], Field(serialization_alias="images", alias="images")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class VectorProperties(pydantic.BaseModel):
    """Supported properties for a vector

    Attributes:
        Geometry: Corresponds to the geometry of the geojson. Defaults to `None`.
    """

    Geometry: Annotated[Optional[str], Field(serialization_alias="geometry", alias="geometry")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class DateProperties(pydantic.BaseModel):
    """Properties of a date

    Attributes:
        FromAoi:
            True if the date is to be taken from the AOI. False, otherwise. Defaults to `None`.
    """

    FromAoi: Annotated[Optional[bool], Field(serialization_alias="from_aoi", alias="from_aoi")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class TabularFileSchema(pydantic.BaseModel):
    """Represents the schema of a table

    Attributes:
        Headers: The ordered list of columns in the table. Defaults to `None`.
    """

    Headers: Annotated[Optional[List[str]], Field(serialization_alias="headers", alias="headers")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class TabularProperties(pydantic.BaseModel):
    """Propertiers for a table

    Attributes:
        FileType:
            Type of the file. Usually, `csv`. Defaults to `None`.
        FileSchema:
            Schema of the table. Defaults to `None`.
    """

    FileType: Annotated[Optional[str], Field(serialization_alias="file_type", alias="file_type")] = None
    FileSchema: Annotated[
        Optional[TabularFileSchema],
        Field(serialization_alias="file_schema", alias="file_schema"),
    ] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


Properties = Union[RasterProperties, VectorProperties, DateProperties, TabularProperties]


FormatPropertyMap = {
    FormatTypes.RASTER.value: RasterProperties,
    FormatTypes.VECTOR.value: VectorProperties,
    FormatTypes.DATE.value: DateProperties,
    FormatTypes.TABULAR.value: TabularProperties,
}


def _PropertiesFromConfig(output_cfg: Dict[str, Any]) -> Optional[Properties]:
    print(output_cfg)
    format = output_cfg["format"]
    props = output_cfg.get("properties")
    if props is None:
        return None
    return FormatPropertyMap[format].model_validate(props)


class ModelInfTimes(pydantic.BaseModel):
    InfStartTime: str
    InfEndTime: str


class Callback(pydantic.BaseModel):
    Id: Annotated[str, Field(serialization_alias="id")]
    State: Annotated[ModelStates, Field(serialization_alias="state")] = ModelStates.INPROGRESS
    Inputs: Annotated[Optional[List[Dict[str, Any]]], Field(serialization_alias="inputs")] = None
    Outputs: Annotated[Optional[List[Dict[str, Any]]], Field(serialization_alias="outputs")] = None
    Result: Annotated[Optional[List[Dict[str, Any]]], Field(serialization_alias="result")] = None
    Logs: Annotated[Optional[str], Field(serialization_alias="logs")] = ""
    UserLogs: Annotated[Optional[str], Field(serialization_alias="user_logs")] = ""
    ErrMsg: Annotated[Optional[str], Field(serialization_alias="err_msg")] = ""
    StartTime: Annotated[Optional[str], Field(serialization_alias="start_time")] = None
    EndTime: Annotated[Optional[str], Field(serialization_alias="end_time")] = None
    BlockInfStartTime: Annotated[Optional[str], Field(serialization_alias="block_inf_start_time")] = None
    BlockInfEndTime: Annotated[Optional[str], Field(serialization_alias="block_inf_end_time")] = None
    FailureType: Annotated[Optional[str], Field(serialization_alias="failure_type")] = None
    Progress: Annotated[Optional[float], Field(serialization_alias="progress", alias="progress")] = None
    model_config = ConfigDict(use_enum_values=False, populate_by_name=True)


class InferenceOpts(pydantic.BaseModel):
    """Stores data whose lifetimes are scoped to a particular
    inference run.

    This data is meant to be used internally by _clay_.

    Attributes:
        Id (str): A uuidv4 string uniquely identifying this inference run.
        InputList (List[Dict[str, Any]]):
            List of inputs provided to the model. This data is used by the runner during callbacks.
        InputPropMap (Dict[str, Any]):
            A dictionary mapping the input names with their values.
    """

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
    IsArtifact: Annotated[Optional[bool], Field(alias="is_artifact", serialization_alias="is_artifact")] = None
    DisplayName: Annotated[Optional[str], Field(alias="display_name", serialization_alias="display_name")] = None
    Description: Annotated[Optional[str], Field(alias="description", serialization_alias="description")] = None
    Metadata: Annotated[
        Optional[Dict[str, str]],
        Field(alias="metadata", serialization_alias="metadata"),
    ] = {}
    Group: Annotated[str, Field(alias="group", serialization_alias="group")] = ""
    model_config = {"validate_assignment": True, "populate_by_name": True}


class Raster(_DataMeta):
    """Type representing `TIFFs` and `GeoTIFFs`"""

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
        metadata: Dict[str, str] = {},
        properties: Optional[RasterProperties] = None,
        type: Union[str, PrimitiveTypes] = PrimitiveTypes.URL.value,
        group: str = "",
        *args: Any,
        **kwargs: Any,
    ):
        """
        Args:
            name (str): Name of the data item
            value (Union[int, float, str, bool]): The value of the raster.Usually a url
            default (Optional[Union[str, int, float, bool]], optional]): Any default
                value. Defaults to None.
            is_artifact (Optional[bool], optional): Signifies whether the raster has a
                supporting asset. Defaults to True.
            metadata (Optional[Dict[str, str]], optional): A map containing an arbitrary
                set of key-value pairs. Ideally, this should not be used. Clay internally
                sets some values to this dict for each housekeeping purposes. If the user
                provides a map as well, the final map attached to the data item would be
                union. Defaults to {}.
            group (str): The common set this output item belongs to. Defaults to "".
            properties (Optional[RasterProperties], optional): Properties of the raster.
                Defaults to None.
        """
        if isinstance(type, str):
            _type = PrimitiveTypes(type)
        else:
            _type = type

        # `Type` is set as best guess here. This would anyway be override based on
        # the output config
        super().__init__(
            Format=FormatTypes.RASTER.value,
            Name=name,
            Value=value,
            Type=PrimitiveTypes.URL.value,
            Default=default,
            IsArtifact=is_artifact,
            Metadata=metadata,
            Group=group,
        )
        __pydantic_self__.Properties = properties


class Vector(_DataMeta):
    """Type representing Vectors i.e. `GeoJSONs`"""

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
        metadata: Dict[str, str] = {},
        group: str = "",
        properties: Optional[VectorProperties] = None,
        type: Union[str, PrimitiveTypes] = PrimitiveTypes.URL.value,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Args:
            name (str): Name of the data item.
            value (str): Value of the file.
            default (Optional[Union[str, int, float, bool]], optional):
                Any default value for this item. Defaults to None.
            is_artifact (Optional[bool], optional):
                True if the data item has a supporting asset. Defaults to True.
            properties (Optional[VectorProperties], optional): Properties of the GeoJSON.
                Defaults to None.
            metadata (Dict[str, str], optional): A map containing an arbitrary set of
                key-value pairs. Ideally, this should not be used. Clay internally sets
                some values to this dict for each housekeeping purposes.
                If the user provides a map as well, the final map attached to the data
                item would be union. Defaults to {}.
            group (str): The common set this output item belongs to. Defaults to "".
        """
        if isinstance(type, str):
            _type = PrimitiveTypes(type)
        else:
            _type = type

        super().__init__(
            Format=FormatTypes.VECTOR.value,
            Type=_type.value,
            Name=name,
            Value=value,
            IsArtifact=is_artifact,
            Default=default,
            Metadata=metadata,
            Group=group,
        )
        __pydantic_self__.Properties = properties


class Date(_DataMeta):
    """Type representing a Date"""

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
        type: Union[str, PrimitiveTypes] = PrimitiveTypes.STR,
        metadata: Dict[str, str] = {},
        group: str = "",
        *args: Any,
        **kwargs: Any,
    ):
        """

        Args:
            name (str): Name of the data item.
            value (str): Value of the item.
            properties (Optional[DateProperties], optional): Properties of the date.
                Defaults to None.
            default (Optional[Union[str, int, float, bool]], optional): _description_.
                Defaults to None.
            metadata (Dict[str, str], optional): A map containing an arbitrary set of
                key-value pairs. Ideally, this should not be used. Clay internally sets
                some values to this dict for each housekeeping purposes. If the user
                provides a map as well, the final map attached to the data item would be
                union. Defaults to {}.
            group (str): The common set this output item belongs to. Defaults to "".
        """
        if isinstance(type, str):
            _type = PrimitiveTypes(type)
        else:
            _type = type
        super().__init__(
            Format=FormatTypes.DATE.value,
            Type=PrimitiveTypes.STR.value,
            Name=name,
            Value=value,
            IsArtifact=False,
            Default=default,
            Metadata=metadata,
            Group=group,
        )
        __pydantic_self__.Properties = properties


class Tabular(_DataMeta):
    """Type representing a table"""

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
        type: Union[str, PrimitiveTypes] = PrimitiveTypes.URL.value,
        metadata: Dict[str, str] = {},
        group: str = "",
        *args: Any,
        **kwargs: Any,
    ):
        """

        Args:
            name (str): Name of the data item.
            value (str): Value of the item.
            is_artifact (Optional[bool], optional): True if the data item has a supporting
            asset. Defaults to True.
            properties (Optional[TabularProperties], optional): Properties of the table.
                Defaults to None.
            default (Optional[Union[str, int, float, bool]], optional): Any default value.
                Defaults to None.
            metadata (Dict[str, str], optional): A map containing an arbitrary set of
                key-value pairs. Ideally, this should not be used. Clay internally sets
                some values to this dict for each housekeeping purposes. If the user
                provides a map as well, the final map attached to the data item would be
                union. Defaults to {}.
           group (str): The common set this output item belongs to. Defaults to "".
        """
        if isinstance(type, str):
            _type = PrimitiveTypes(type)
        else:
            _type = type

        super().__init__(
            Format=FormatTypes.TABULAR.value,
            Value=value,
            Name=name,
            Type=PrimitiveTypes.URL.value,
            IsArtifact=is_artifact,
            Default=default,
            Metadata=metadata,
            Group=group,
        )
        __pydantic_self__.Properties = properties


class String(_DataMeta):
    """Type representing a string."""

    # pydantic throws error without this
    __null__: Any

    def __init__(
        __pydantic_self__,
        name: str,
        value: Optional[str] = None,
        default: Optional[Union[str, int, float, bool]] = None,
        type: Union[str, PrimitiveTypes] = PrimitiveTypes.STR,
        metadata: Dict[str, str] = {},
        group: str = "",
        *args: Any,
        **kwargs: Any,
    ):
        """
        Args:
            name (str): Name of the data item.
            value (Optional[str], optional): Value of the data item. Defaults to `None`.
            default (Optional[Union[str, int, float, bool]], optional): Ant default value.
                Defaults to None.
            metadata (Dict[str, str], optional): A map containing an arbitrary set of
                key-value pairs. Ideally, this should not be used. Clay internally sets
                some values to this dict for each housekeeping purposes. If the user
                provides a map as well, the final map attached to the data item
                would be union. Defaults to {}.
            group (str): The common set this output item belongs to. Defaults to "".
        """
        if isinstance(type, str):
            _type = PrimitiveTypes(type)
        else:
            _type = type

        super().__init__(
            Format=FormatTypes.STRING.value,
            Name=name,
            Type=PrimitiveTypes.STR.value,
            Value=value,
            IsArtifact=False,
            Default=default,
            Metadata=metadata,
            Group=group,
        )


class Number(_DataMeta):
    """Type representing a number."""

    # pydantic throws error without this
    __null__: Any

    def __init__(
        __pydantic_self__,
        name: str,
        value: Union[int, float, None] = None,
        default: Optional[Union[str, int, float, bool]] = None,
        type: Union[str, PrimitiveTypes] = PrimitiveTypes.FLOAT,
        metadata: Dict[str, str] = {},
        group: str = "",
        *args: Any,
        **kwargs: Any,
    ):
        """

        Args:
            name (str): Name of the data item.
            value (Union[int, float, None], optional): Value of the data item.
                Defaults to None.
            default (Optional[Union[str, int, float, bool]], optional): Any default value.
                Defaults to None.
            metadata (Dict[str, str], optional): A map containing an arbitrary set of
                key-value pairs. Ideally, this should not be used. Clay internally sets
                some values to this dict for each housekeeping purposes.
                If the user provides a map as well, the final map attached to the data
                item would be union. Defaults to {}.
            group (str): The common set this output item belongs to. Defaults to "".
        """
        if isinstance(type, str):
            _type = PrimitiveTypes(type)
        else:
            _type = type

        super().__init__(
            Format=FormatTypes.NUMBER.value,
            Name=name,
            Type=PrimitiveTypes.FLOAT.value,
            Value=value,
            IsArtifact=False,
            Default=default,
            Metadata=metadata,
            Group=group,
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


def _serialize_output_buffer(b: OutputsBuffer) -> List[Dict[str, Any]]:
    l = []  # noqa: E741
    for o in b:
        l.append(o.model_dump(by_alias=True, exclude_none=True))
    return l
