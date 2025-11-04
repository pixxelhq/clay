from typing import ClassVar as _ClassVar
from typing import Iterable as _Iterable
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import Union as _Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

DESCRIPTOR: _descriptor.FileDescriptor

class Version(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    v2: _ClassVar[Version]

class Format(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    raster: _ClassVar[Format]
    vector: _ClassVar[Format]
    tabular: _ClassVar[Format]
    string: _ClassVar[Format]
    number: _ClassVar[Format]
    date: _ClassVar[Format]

class VizTypes(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    continuous: _ClassVar[VizTypes]
    bucket: _ClassVar[VizTypes]
    discrete: _ClassVar[VizTypes]
v2: Version
raster: Format
vector: Format
tabular: Format
string: Format
number: Format
date: Format
continuous: VizTypes
bucket: VizTypes
discrete: VizTypes

class ListOfFloats(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, values: _Optional[_Iterable[float]] = ...) -> None: ...

class Range(_message.Message):
    __slots__ = ("min", "max")
    MIN_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    min: float
    max: float
    def __init__(self, min: _Optional[float] = ..., max: _Optional[float] = ...) -> None: ...

class ContinuousViz(_message.Message):
    __slots__ = ("color_map_name", "bandwise_range")
    COLOR_MAP_NAME_FIELD_NUMBER: _ClassVar[int]
    BANDWISE_RANGE_FIELD_NUMBER: _ClassVar[int]
    color_map_name: str
    bandwise_range: _containers.RepeatedCompositeFieldContainer[Range]
    def __init__(self, color_map_name: _Optional[str] = ..., bandwise_range: _Optional[_Iterable[_Union[Range, _Mapping]]] = ...) -> None: ...

class Bucket(_message.Message):
    __slots__ = ("color_code", "min", "max")
    COLOR_CODE_FIELD_NUMBER: _ClassVar[int]
    MIN_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    color_code: str
    min: float
    max: float
    def __init__(self, color_code: _Optional[str] = ..., min: _Optional[float] = ..., max: _Optional[float] = ...) -> None: ...

class ListOfBuckets(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Bucket]
    def __init__(self, items: _Optional[_Iterable[_Union[Bucket, _Mapping]]] = ...) -> None: ...

class BucketViz(_message.Message):
    __slots__ = ("bandwise",)
    BANDWISE_FIELD_NUMBER: _ClassVar[int]
    bandwise: _containers.RepeatedCompositeFieldContainer[ListOfBuckets]
    def __init__(self, bandwise: _Optional[_Iterable[_Union[ListOfBuckets, _Mapping]]] = ...) -> None: ...

class Visualization(_message.Message):
    __slots__ = ("type", "continuous", "bucket", "discrete")
    class DiscreteEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CONTINUOUS_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    DISCRETE_FIELD_NUMBER: _ClassVar[int]
    type: VizTypes
    continuous: ContinuousViz
    bucket: BucketViz
    discrete: _containers.ScalarMap[str, str]
    def __init__(self, type: _Optional[_Union[VizTypes, str]] = ..., continuous: _Optional[_Union[ContinuousViz, _Mapping]] = ..., bucket: _Optional[_Union[BucketViz, _Mapping]] = ..., discrete: _Optional[_Mapping[str, str]] = ...) -> None: ...

class DiscretizationClass(_message.Message):
    __slots__ = ("color", "name", "value", "range")
    COLOR_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    RANGE_FIELD_NUMBER: _ClassVar[int]
    color: str
    name: str
    value: str
    range: Range
    def __init__(self, color: _Optional[str] = ..., name: _Optional[str] = ..., value: _Optional[str] = ..., range: _Optional[_Union[Range, _Mapping]] = ...) -> None: ...

class Discretization(_message.Message):
    __slots__ = ("type", "classes")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CLASSES_FIELD_NUMBER: _ClassVar[int]
    type: str
    classes: _containers.RepeatedCompositeFieldContainer[DiscretizationClass]
    def __init__(self, type: _Optional[str] = ..., classes: _Optional[_Iterable[_Union[DiscretizationClass, _Mapping]]] = ...) -> None: ...

class RasterProperties(_message.Message):
    __slots__ = ("bands", "source", "collection", "dtype", "satellite_look_angle", "sun_elevation", "visualisation", "date", "discretization", "images")
    BANDS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    COLLECTION_FIELD_NUMBER: _ClassVar[int]
    DTYPE_FIELD_NUMBER: _ClassVar[int]
    SATELLITE_LOOK_ANGLE_FIELD_NUMBER: _ClassVar[int]
    SUN_ELEVATION_FIELD_NUMBER: _ClassVar[int]
    VISUALISATION_FIELD_NUMBER: _ClassVar[int]
    DATE_FIELD_NUMBER: _ClassVar[int]
    DISCRETIZATION_FIELD_NUMBER: _ClassVar[int]
    IMAGES_FIELD_NUMBER: _ClassVar[int]
    bands: _containers.RepeatedScalarFieldContainer[str]
    source: str
    collection: str
    dtype: str
    satellite_look_angle: float
    sun_elevation: float
    visualisation: Visualization
    date: str
    discretization: Discretization
    images: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, bands: _Optional[_Iterable[str]] = ..., source: _Optional[str] = ..., collection: _Optional[str] = ..., dtype: _Optional[str] = ..., satellite_look_angle: _Optional[float] = ..., sun_elevation: _Optional[float] = ..., visualisation: _Optional[_Union[Visualization, _Mapping]] = ..., date: _Optional[str] = ..., discretization: _Optional[_Union[Discretization, _Mapping]] = ..., images: _Optional[_Iterable[str]] = ...) -> None: ...

class AssetSource(_message.Message):
    __slots__ = ("id", "type", "layer_name")
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    LAYER_NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    type: str
    layer_name: str
    def __init__(self, id: _Optional[str] = ..., type: _Optional[str] = ..., layer_name: _Optional[str] = ...) -> None: ...

class Raster(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "default", "value", "area", "asset_source", "properties", "version", "stac_url")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    AREA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    STAC_URL_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    default: str
    value: str
    area: float
    asset_source: AssetSource
    properties: RasterProperties
    version: Version
    stac_url: str
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., default: _Optional[str] = ..., value: _Optional[str] = ..., area: _Optional[float] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., properties: _Optional[_Union[RasterProperties, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ..., stac_url: _Optional[str] = ...) -> None: ...

class VectorProperties(_message.Message):
    __slots__ = ("geometry",)
    GEOMETRY_FIELD_NUMBER: _ClassVar[int]
    geometry: str
    def __init__(self, geometry: _Optional[str] = ...) -> None: ...

class Vector(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "default", "value", "area", "asset_source", "properties", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    AREA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    default: str
    value: str
    area: float
    asset_source: AssetSource
    properties: VectorProperties
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., default: _Optional[str] = ..., value: _Optional[str] = ..., area: _Optional[float] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., properties: _Optional[_Union[VectorProperties, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class TabularFileSchema(_message.Message):
    __slots__ = ("headers",)
    HEADERS_FIELD_NUMBER: _ClassVar[int]
    headers: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, headers: _Optional[_Iterable[str]] = ...) -> None: ...

class TabularProperties(_message.Message):
    __slots__ = ("file_type", "file_schema")
    FILE_TYPE_FIELD_NUMBER: _ClassVar[int]
    FILE_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    file_type: str
    file_schema: TabularFileSchema
    def __init__(self, file_type: _Optional[str] = ..., file_schema: _Optional[_Union[TabularFileSchema, _Mapping]] = ...) -> None: ...

class Tabular(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "default", "value", "area", "asset_source", "properties", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    AREA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    default: str
    value: str
    area: float
    asset_source: AssetSource
    properties: TabularProperties
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., default: _Optional[str] = ..., value: _Optional[str] = ..., area: _Optional[float] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., properties: _Optional[_Union[TabularProperties, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class DateProperties(_message.Message):
    __slots__ = ("from_aoi",)
    FROM_AOI_FIELD_NUMBER: _ClassVar[int]
    from_aoi: bool
    def __init__(self, from_aoi: bool = ...) -> None: ...

class Date(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "default", "value", "area", "asset_source", "properties", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    AREA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    default: str
    value: str
    area: float
    asset_source: AssetSource
    properties: DateProperties
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., default: _Optional[str] = ..., value: _Optional[str] = ..., area: _Optional[float] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., properties: _Optional[_Union[DateProperties, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class String(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "default", "value", "area", "asset_source", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    AREA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    default: str
    value: str
    area: float
    asset_source: AssetSource
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., default: _Optional[str] = ..., value: _Optional[str] = ..., area: _Optional[float] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class Number(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "default", "value", "area", "asset_source", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    AREA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    default: str
    value: str
    area: float
    asset_source: AssetSource
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., default: _Optional[str] = ..., value: _Optional[str] = ..., area: _Optional[float] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class RasterSpec(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "asset_source", "properties", "validation", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    asset_source: AssetSource
    properties: RasterProperties
    validation: RasterValidation
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., properties: _Optional[_Union[RasterProperties, _Mapping]] = ..., validation: _Optional[_Union[RasterValidation, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class VectorSpec(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "asset_source", "properties", "validation", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    asset_source: AssetSource
    properties: VectorProperties
    validation: VectorValidation
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., properties: _Optional[_Union[VectorProperties, _Mapping]] = ..., validation: _Optional[_Union[VectorValidation, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class TabularSpec(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "asset_source", "properties", "validation", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    asset_source: AssetSource
    properties: TabularProperties
    validation: TabularValidation
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., properties: _Optional[_Union[TabularProperties, _Mapping]] = ..., validation: _Optional[_Union[TabularValidation, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class DateSpec(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "asset_source", "properties", "validation", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    asset_source: AssetSource
    properties: DateProperties
    validation: DateValidation
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., properties: _Optional[_Union[DateProperties, _Mapping]] = ..., validation: _Optional[_Union[DateValidation, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class StringSpec(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "asset_source", "validation", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    asset_source: AssetSource
    validation: StringValidation
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., validation: _Optional[_Union[StringValidation, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class NumberSpec(_message.Message):
    __slots__ = ("format", "type", "name", "description", "display_name", "is_artifact", "group", "metadata", "asset_source", "validation", "version")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ASSET_SOURCE_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    format: Format
    type: str
    name: str
    description: str
    display_name: str
    is_artifact: bool
    group: str
    metadata: _containers.ScalarMap[str, str]
    asset_source: AssetSource
    validation: NumberValidation
    version: Version
    def __init__(self, format: _Optional[_Union[Format, str]] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., display_name: _Optional[str] = ..., is_artifact: bool = ..., group: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., asset_source: _Optional[_Union[AssetSource, _Mapping]] = ..., validation: _Optional[_Union[NumberValidation, _Mapping]] = ..., version: _Optional[_Union[Version, str]] = ...) -> None: ...

class RasterValidation(_message.Message):
    __slots__ = ("min_area", "max_area")
    MIN_AREA_FIELD_NUMBER: _ClassVar[int]
    MAX_AREA_FIELD_NUMBER: _ClassVar[int]
    min_area: float
    max_area: float
    def __init__(self, min_area: _Optional[float] = ..., max_area: _Optional[float] = ...) -> None: ...

class VectorValidation(_message.Message):
    __slots__ = ("min_area", "max_area")
    MIN_AREA_FIELD_NUMBER: _ClassVar[int]
    MAX_AREA_FIELD_NUMBER: _ClassVar[int]
    min_area: float
    max_area: float
    def __init__(self, min_area: _Optional[float] = ..., max_area: _Optional[float] = ...) -> None: ...

class TabularValidation(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DateValidation(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StringValidation(_message.Message):
    __slots__ = ("regex_match",)
    REGEX_MATCH_FIELD_NUMBER: _ClassVar[int]
    regex_match: str
    def __init__(self, regex_match: _Optional[str] = ...) -> None: ...

class NumberValidation(_message.Message):
    __slots__ = ("min_value", "max_value")
    MIN_VALUE_FIELD_NUMBER: _ClassVar[int]
    MAX_VALUE_FIELD_NUMBER: _ClassVar[int]
    min_value: float
    max_value: float
    def __init__(self, min_value: _Optional[float] = ..., max_value: _Optional[float] = ...) -> None: ...
