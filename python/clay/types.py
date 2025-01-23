from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import datatypes
import pydantic
from pydantic import ConfigDict, Field
from typing_extensions import Annotated

PARAMETER_ATTR_NAME = "parameter"
PERSISTENT_ATTR_NAME = "persistent"
_IS_ARTIFACT_ATTR_NAME = "is_artifact"
EXECUTOR_ENVVAR = "EXECUTOR"


class _CommonEnvvars(str, Enum):
    ORCHESTRATOR_URL = "ORCHESTRATOR_URL"
    DEXTER_HOST = "DEXTER_HOST"
    DEXTER_PORT = "DEXTER_PORT"
    TASK_ID = "task_id"
    DEXTER_RUN_TYPE = "DEXTER_RUN_TYPE"


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

    def to_types_v2(self):
        dc = datatypes.DiscretizationClass()
        dc.color = self.Color or ""
        dc.name = self.Name or ""

        if self.Value:
            dc.value = self.Value or ""
        if self.Range:
            dc.range.min = self.Range[0]
            dc.range.max = self.Range[1]
        return dc

    @staticmethod
    def from_types_v2(t: datatypes.DiscretizationClass):
        dc = DiscretizationItem()
        dc.Color = t.color
        dc.Name = t.name
        dc.Value = None if t.value == "" else t.value
        if t.range is not None:
            dc.Range = [t.range.min, t.range.max]
        else:
            dc.Range = None
        return dc


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

    def to_types_v2(self):
        classes = []
        rd_v2 = datatypes.Discretization()
        assert self.Classes is not None
        for ci in self.Classes:
            classes.append(ci.to_types_v2())
        rd_v2.type = self.Type or ""
        rd_v2.classes.extend(classes)
        return rd_v2

    @staticmethod
    def from_types_v2(t: datatypes.Discretization):
        rd = RasterDiscretization()
        rd.Type = t.type
        classes = []
        for ci in t.classes:
            classes.append(DiscretizationItem.from_types_v2(ci))
        rd.Classes = classes
        return rd


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

    def to_types_v2(self) -> datatypes.ContinuousViz:
        vc_v2 = datatypes.ContinuousViz(color_map_name=self.ColorMapName)
        assert self.Range is not None
        bandwise_range = []
        for band in self.Range:
            bandwise_range.append(datatypes.Range(min=band[0], max=band[1]))
        vc_v2.bandwise_range.extend(bandwise_range)
        return vc_v2

    @staticmethod
    def from_types_v2(t: datatypes.ContinuousViz):
        vc = VizContinuous()
        vc.ColorMapName = t.color_map_name
        bandwise_range = []
        for band in t.bandwise_range:
            bandwise_range.append([band.min, band.max])
        vc.Range = bandwise_range
        return vc

    def _is_zero_valued_go(self) -> bool:
        """Why: Since Continuous field in the V1 raster (as defined in Orchestrator Go) is of concrete value,
        and not pointer. As a result it will always send a zero-valued struct for this field which is incompatible
        with v2 spec, since here it can be optional.
        """
        return self.ColorMapName == "" and self.Range is None


class VizBucket(pydantic.BaseModel):
    """Supported visualisation for histograms.

    Attributes:
        Range (Annotated[Optional[List[float]]]): Range of the pixel values in the format [min, max].
        ColorCode (Annotated[Optional[str]]): Hex code of the color.
    """

    Range: Annotated[Optional[List[float]], Field(serialization_alias="range", alias="range")] = None
    ColorCode: Annotated[Optional[str], Field(serialization_alias="color", alias="color")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    def to_types_v2(self):
        bucket_v2 = datatypes.Bucket()
        assert self.Range is not None
        bucket_v2.min = self.Range[0]
        bucket_v2.max = self.Range[1]
        bucket_v2.color_code = self.ColorCode or ""
        return bucket_v2

    @staticmethod
    def from_types_v2(t: datatypes.Bucket):
        vb = VizBucket()
        vb.ColorCode = t.color_code
        if t.min is not None and t.max is not None:
            vb.Range = [t.min, t.max]
        else:
            vb.Range = None
        return vb


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

    def to_types_v2(self):
        t = datatypes.VizTypes.Name(datatypes.VizTypes.Value(self.Type or ""))
        viz_v2 = datatypes.Visualization(type=t)
        if self.Continuous and not self.Continuous._is_zero_valued_go():
            viz_v2.continuous.CopyFrom(self.Continuous.to_types_v2())
        if self.Discrete and len(self.Discrete) > 0:
            viz_v2.discrete.update(self.Discrete)
        if self.Bucket and len(self.Bucket) > 0:
            bandwise = []
            for band in self.Bucket:
                items = []
                for bucket in band:
                    items.append(bucket.to_types_v2())
                bandwise.append(datatypes.ListOfBuckets(items=items))
            viz_v2.bucket.bandwise.extend(bandwise)
        return viz_v2

    @staticmethod
    def from_types_v2(t: datatypes.Visualization):
        rv = RasterVisualisation(Continuous=None, Bucket=None, Discrete=None)
        rv.Type = datatypes.VizTypes.Name(t.type)
        if t.continuous.IsInitialized():
            rv.Continuous = VizContinuous.from_types_v2(t.continuous)
        if t.discrete:
            rv.Discrete = dict(t.discrete) if t.discrete and len(t.discrete) else None
        if t.bucket.IsInitialized():
            bandwise = []
            for band in t.bucket.bandwise:
                items = []
                for bucket in band.items:
                    items.append(VizBucket.from_types_v2(bucket))
                bandwise.append(items)
            rv.Bucket = bandwise if len(bandwise) > 0 else None
        return rv


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

    def to_types_v2(self) -> datatypes.RasterProperties:
        rp_v2 = datatypes.RasterProperties()

        if self.Bands is not None:
            rp_v2.bands.extend(self.Bands)
        if self.Images is not None:
            rp_v2.images.extend(self.Images)

        rp_v2.collection = self.Collection or ""
        rp_v2.source = self.Source or ""
        rp_v2.date = self.Date or ""
        rp_v2.dtype = self.Dtype or ""

        if self.SatelliteLookAngle:
            rp_v2.satellite_look_angle = self.SatelliteLookAngle  # type: ignore
        if self.SunElevation:
            rp_v2.sun_elevation = self.SunElevation  # type: ignore

        rp_v2.date = self.Date or ""

        if self.Visualisation:
            assert self.Visualisation is not None
            rp_v2.visualisation.CopyFrom(self.Visualisation.to_types_v2())

        if self.Discretization:
            assert self.Discretization is not None
            rp_v2.discretization.CopyFrom(self.Discretization.to_types_v2())

        return rp_v2

    @staticmethod
    def from_types_v2(t: datatypes.RasterProperties):
        rp = RasterProperties()
        rp.Bands = list(t.bands)
        rp.Collection = t.collection
        rp.Source = t.source
        rp.Date = t.date
        rp.Dtype = t.dtype
        rp.SunElevation = t.sun_elevation
        rp.SatelliteLookAngle = t.satellite_look_angle
        rp.Images = list(t.images)
        if t.HasField("visualisation") and t.visualisation:
            rp.Visualisation = RasterVisualisation.from_types_v2(t.visualisation)
        if t.HasField("discretization") and t.discretization:
            rp.Discretization = RasterDiscretization.from_types_v2(t.discretization)
        return rp


class VectorProperties(pydantic.BaseModel):
    """Supported properties for a vector

    Attributes:
        Geometry: Corresponds to the geometry of the geojson. Defaults to `None`.
    """

    Geometry: Annotated[Optional[str], Field(serialization_alias="geometry", alias="geometry")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    def to_types_v2(self) -> datatypes.VectorProperties:
        vp_v2 = datatypes.VectorProperties()
        vp_v2.geometry = self.Geometry or ""
        return vp_v2

    @staticmethod
    def from_types_v2(t: datatypes.VectorProperties):
        vp = VectorProperties()
        vp.Geometry = t.geometry
        return vp


class DateProperties(pydantic.BaseModel):
    """Properties of a date

    Attributes:
        FromAoi:
            True if the date is to be taken from the AOI. False, otherwise. Defaults to `None`.
    """

    FromAoi: Annotated[Optional[bool], Field(serialization_alias="from_aoi", alias="from_aoi")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    def to_types_v2(self) -> datatypes.DateProperties:
        dp_v2 = datatypes.DateProperties()
        dp_v2.from_aoi = self.FromAoi or False
        return dp_v2

    @staticmethod
    def from_types_v2(t: datatypes.DateProperties):
        dp = DateProperties()
        dp.FromAoi = t.from_aoi
        return dp


class TabularFileSchema(pydantic.BaseModel):
    """Represents the schema of a table

    Attributes:
        Headers: The ordered list of columns in the table. Defaults to `None`.
    """

    Headers: Annotated[Optional[List[str]], Field(serialization_alias="headers", alias="headers")] = None

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    def to_types_v2(self):
        tbf_v2 = datatypes.TabularFileSchema()
        if self.Headers:
            tbf_v2.headers.extend(self.Headers)
        return tbf_v2

    @staticmethod
    def from_types_v2(t: datatypes.TabularFileSchema):
        tbf = TabularFileSchema()
        tbf.Headers = list(t.headers)
        return tbf


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

    def to_types_v2(self) -> datatypes.TabularProperties:
        tb_v2 = datatypes.TabularProperties()
        tb_v2.file_type = self.FileType or ""
        if self.FileSchema:
            tb_v2.file_schema.CopyFrom(self.FileSchema.to_types_v2())
        return tb_v2

    @staticmethod
    def from_types_v2(t: datatypes.TabularProperties):
        tb = TabularProperties()
        tb.FileType = t.file_type
        if t.HasField("file_schema") and t.file_schema:
            tb.FileSchema = TabularFileSchema.from_types_v2(t.file_schema)
        return tb


Properties = Union[RasterProperties, VectorProperties, DateProperties, TabularProperties]

FormatPropertyMap = {
    FormatTypes.RASTER.value: RasterProperties,
    FormatTypes.VECTOR.value: VectorProperties,
    FormatTypes.DATE.value: DateProperties,
    FormatTypes.TABULAR.value: TabularProperties,
}


def _PropertiesFromConfig(output_cfg: Dict[str, Any], force_to_v2: bool = False) -> Optional[Properties]:
    print("###### ", output_cfg)
    format = output_cfg["format"]
    props = output_cfg.get("properties")
    if props is None:
        return None

    properties: Properties = FormatPropertyMap[format].model_validate(props)
    return properties


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

    def to_types_v2(self) -> datatypes.DataWrapper:
        r = datatypes.Raster()
        r.format = datatypes.raster
        r.type = self.Type or ""
        r.name = self.Name
        r.display_name = self.DisplayName or ""
        r.description = self.Description or ""
        r.is_artifact = self.IsArtifact or False
        r.group = self.Group
        r.default = str(self.Default or "")
        r.version = datatypes.Version.v2

        if self.Metadata is not None:
            assert self.Metadata is not None
            r.metadata.update(self.Metadata)

        r.value = str(self.Value or "")

        if self.Properties:
            assert self.Properties is not None
            r.properties.CopyFrom(self.Properties.to_types_v2())
        return datatypes.DataWrapper(r)

    @staticmethod
    def from_types_v2(t: datatypes.Raster):
        r = Raster(name=t.name, value=t.value)
        r.DisplayName = t.display_name
        r.Description = t.description
        r.IsArtifact = t.is_artifact
        r.Group = t.group
        r.Default = t.default
        r.Metadata = dict(t.metadata)
        if t.HasField("properties") and t.properties:
            r.Properties = RasterProperties.from_types_v2(t.properties)
        else:
            r.Properties = None
        return r


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

    def to_types_v2(self) -> datatypes.DataWrapper:
        v = datatypes.Vector()
        v.format = datatypes.vector
        v.type = self.Type or ""
        v.name = self.Name
        v.display_name = self.DisplayName or ""
        v.description = self.Description or ""
        v.is_artifact = self.IsArtifact or False
        v.group = self.Group
        v.default = str(self.Default or "")
        v.version = datatypes.Version.v2

        if self.Metadata is not None:
            assert self.Metadata is not None
            v.metadata.update(self.Metadata)

        v.value = str(self.Value or "")

        if self.Properties:
            v.properties.CopyFrom(self.Properties.to_types_v2())
        return datatypes.DataWrapper(v)

    @staticmethod
    def from_types_v2(t: datatypes.Vector):
        v = Vector(name=t.name, value=t.value)
        v.DisplayName = t.display_name
        v.Description = t.description
        v.IsArtifact = t.is_artifact
        v.Group = t.group
        v.Default = t.default
        v.Metadata = dict(t.metadata)
        if t.HasField("properties") and t.properties:
            v.Properties = VectorProperties.from_types_v2(t.properties)
        else:
            v.Properties = None
        return v


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

    def to_types_v2(self) -> datatypes.DataWrapper:
        d = datatypes.Date()
        d.format = datatypes.date
        d.type = self.Type or ""
        d.name = self.Name
        d.display_name = self.DisplayName or ""
        d.description = self.Description or ""
        d.is_artifact = self.IsArtifact or False
        d.group = self.Group
        d.default = str(self.Default or "")
        d.version = datatypes.Version.v2

        if self.Metadata is not None:
            assert self.Metadata is not None
            d.metadata.update(self.Metadata)

        d.value = str(self.Value or "")

        if self.Properties:
            d.properties.CopyFrom(self.Properties.to_types_v2())
        return datatypes.DataWrapper(d)

    @staticmethod
    def from_types_v2(t: datatypes.Date):
        d = Date(name=t.name, value=t.value)
        d.DisplayName = t.display_name
        d.Description = t.description
        d.IsArtifact = t.is_artifact
        d.Group = t.group
        d.Default = t.default
        d.Metadata = dict(t.metadata)
        if t.HasField("properties") and t.properties:
            d.Properties = DateProperties.from_types_v2(t.properties)
        else:
            d.Properties = None
        return d


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

    def to_types_v2(self) -> datatypes.DataWrapper:
        t = datatypes.Tabular()
        t.format = datatypes.tabular
        t.type = self.Type or ""
        t.name = self.Name
        t.display_name = self.DisplayName or ""
        t.description = self.Description or ""
        t.is_artifact = self.IsArtifact or False
        t.group = self.Group
        t.version = datatypes.Version.v2

        if self.Metadata is not None:
            assert self.Metadata is not None
            t.metadata.update(self.Metadata)

        t.value = str(self.Value or "")

        if self.Properties:
            t.properties.CopyFrom(self.Properties.to_types_v2())
        return datatypes.DataWrapper(t)

    @staticmethod
    def from_types_v2(t: datatypes.Tabular):
        tl = Tabular(name=t.name, value=t.value)
        tl.DisplayName = t.display_name
        tl.Description = t.description
        tl.IsArtifact = t.is_artifact
        tl.Group = t.group
        tl.Default = t.default
        tl.Metadata = dict(t.metadata)
        if t.HasField("properties") and t.properties:
            tl.Properties = TabularProperties.from_types_v2(t.properties)
        else:
            tl.Properties = None
        return tl


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

    def to_types_v2(self) -> datatypes.DataWrapper:
        s = datatypes.String()
        s.format = datatypes.string
        s.type = self.Type or ""
        s.name = self.Name
        s.display_name = self.DisplayName or ""
        s.description = self.Description or ""
        s.is_artifact = self.IsArtifact or False
        s.group = self.Group
        s.version = datatypes.Version.v2

        if self.Metadata is not None:
            assert self.Metadata is not None
            s.metadata.update(self.Metadata)

        s.value = str(self.Value or "")

        return datatypes.DataWrapper(s)

    @staticmethod
    def from_types_v2(t: datatypes.String):
        s = String(name=t.name, value=t.value)
        s.DisplayName = t.display_name
        s.Description = t.description
        s.IsArtifact = t.is_artifact
        s.Group = t.group
        s.Default = t.default
        s.Metadata = dict(t.metadata)
        return s


class Number(_DataMeta):
    """Type representing a number."""

    # pydantic throws error without this
    __null__: Any

    def __init__(
        __pydantic_self__,
        name: str,
        value: Union[str, int, float, None] = None,
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

    def to_types_v2(self) -> datatypes.DataWrapper:
        n = datatypes.Number()
        n.format = datatypes.number
        n.type = self.Type or ""
        n.name = self.Name
        n.display_name = self.DisplayName or ""
        n.description = self.Description or ""
        n.is_artifact = self.IsArtifact or False
        n.group = self.Group
        n.version = datatypes.Version.v2

        if self.Metadata is not None:
            assert self.Metadata is not None
            n.metadata.update(self.Metadata)

        n.value = str(self.Value or "")

        return datatypes.DataWrapper(n)

    @staticmethod
    def from_types_v2(t: datatypes.Number):
        n = Number(name=t.name, value=t.value)
        n.DisplayName = t.display_name
        n.Description = t.description
        n.IsArtifact = t.is_artifact
        n.Group = t.group
        n.Default = t.default
        n.Metadata = dict(t.metadata)
        return n


class LegacyTypeWrapper(datatypes.DataWrapperInterface):
    def __init__(self, t: Data) -> None:
        self._legacy_type: Data = t

        self._alias_field_mapping: Dict[str, str] = {}
        for field, meta in self._legacy_type.model_fields.items():
            assert meta.alias is not None
            self._alias_field_mapping[meta.alias] = field

    @property
    def DATA(self):  # type: ignore
        return self._legacy_type

    def get_type(self) -> str:
        return self._legacy_type.Type  # type: ignore

    def get_name(self) -> str:
        return self._legacy_type.Name

    def get_format(self) -> str:
        return self._legacy_type.Format

    def serialize_to_dict(self) -> Dict[str, Any]:
        return self._legacy_type.model_dump(by_alias=True)

    def serialize_to_json(self) -> str:
        return self._legacy_type.model_dump_json(by_alias=True)

    def get_value(self) -> str:
        return str(self._legacy_type.Value)

    def set_value(self, value: str) -> None:
        self._legacy_type.Value = value

    def get_default(self) -> str:
        return str(self._legacy_type.Default)

    def get_is_artifact(self) -> bool:
        return self._legacy_type.IsArtifact  # type: ignore

    def set_properties(self, value: Union[Properties, Dict[str, Any], None]) -> None:  # type: ignore
        f = self._alias_field_mapping["properties"]

        if value is None:
            setattr(self._legacy_type, f, None)
            return

        val: Optional[Properties] = None
        if isinstance(value, datatypes.RasterProperties):
            val = RasterProperties.from_types_v2(value)
        elif isinstance(value, datatypes.VectorProperties):
            val = VectorProperties.from_types_v2(value)
        elif isinstance(value, datatypes.DateProperties):
            val = DateProperties.from_types_v2(value)
        elif isinstance(value, datatypes.TabularProperties):
            val = TabularProperties.from_types_v2(value)

        setattr(self._legacy_type, f, val)

    def set_field(self, field: str, value: Any) -> None:
        f = self._alias_field_mapping[field]
        setattr(self._legacy_type, f, value)

    def get_field(self, field: str) -> Any:
        f = self._alias_field_mapping.get(field, None)
        if not f:
            return None
        return getattr(self._legacy_type, f)


Data = Union[Raster, Vector, Date, Tabular, String, Number]

_FormatModelMap = {
    FormatTypes.RASTER.value: Raster,
    FormatTypes.VECTOR.value: Vector,
    FormatTypes.DATE.value: Date,
    FormatTypes.NUMBER.value: Number,
    FormatTypes.STRING.value: String,
    FormatTypes.TABULAR.value: Tabular,
}

OutputBufferItem = Union[Data, datatypes.Data, LegacyTypeWrapper, datatypes.DataWrapper]
OutputsBuffer = List[OutputBufferItem]


def _serialize_output_buffer(
    b: List[datatypes.DataWrapperInterface],
) -> List[Dict[str, Any]]:
    l = []  # noqa: E741
    for o in b:
        l.append(o.serialize_to_dict())
    return l
