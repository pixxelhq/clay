# Datatypes

Pixxel datatypes provide a strongly-typed interface for working with various data formats in Clay models. The datatypes package includes protocol buffer definitions and wrapper classes for both Python and Go.

## Overview

Datatypes are used to define inputs and outputs in your Clay model specifications. They provide validation, serialization, and type safety for different data formats including raster, vector, tabular, and scalar types.

## Available Data Formats

### Raster
Raster represents a TIFF/GeoTIFF data type


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.raster |
| type | [string](#string) | optional | Type of the raster data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the raster |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [Raster.MetadataEntry](#raster.metadataentry) | repeated | Additional metadata key-value pairs |
| default | [string](#string) | optional | Default value if any |
| value | [string](#string) | optional | Actual raster data/URL |
| area | [double](#double) | optional | Area covered by the raster in sq meters |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| properties | [RasterProperties](#rasterproperties) | optional | Raster-specific properties |
| version | [Version](#version) | optional | Schema version |
| stac_url | [string](#string) | optional | STAC item URL |

**Example:**
```python
from datatypes import Raster

raster_data = Raster(
    name="input_image",
    type="geotiff",
    stac_url="stac_collection/url"
    is_artifact=True,
    properties=RasterProperties(
        bands=["B02", "B03", "B04"],
        source="sentinel-2"
    )
)
```

### Vector
Vector represents a GeoJSON data type


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.vector |
| type | [string](#string) | optional | Type of the vector data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the vector |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [Vector.MetadataEntry](#vector.metadataentry) | repeated | Additional metadata key-value pairs |
| default | [string](#string) | optional | Default value if any |
| value | [string](#string) | optional | Actual vector data/URL |
| area | [double](#double) | optional | Area covered by the vector in sq meters |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| properties | [VectorProperties](#vectorproperties) | optional | Vector-specific properties |
| version | [Version](#version) | optional | Schema version |

**Example:**
```python
from datatypes import Vector

vector_data = Vector(
    name="boundary",
    type="geojson",
    value="s3://bucket/path/to/boundary.geojson",
    is_artifact=True,
    properties=VectorProperties(geometry="Polygon")
)
```

### Tabular
Tabular represents table-based data like CSV


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.tabular |
| type | [string](#string) | optional | Type of the tabular data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the tabular data |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [Tabular.MetadataEntry](#tabular.metadataentry) | repeated | Additional metadata key-value pairs |
| default | [string](#string) | optional | Default value if any |
| value | [string](#string) | optional | Actual tabular data/URL |
| area | [double](#double) | optional | Area covered by the tabular data in sq meters |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| properties | [TabularProperties](#tabularproperties) | optional | Tabular-specific properties |
| version | [Version](#version) | optional | Schema version |

**Example:**
```python
from datatypes import Tabular

table_data = Tabular(
    name="results",
    type="csv",
    value="s3://bucket/path/to/results.csv"
)
```

### String
String represents string data types


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.string |
| type | [string](#string) | optional | Type of the string data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the string data |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [String.MetadataEntry](#string.metadataentry) | repeated | Additional metadata key-value pairs |
| default | [string](#string) | optional | Default value if any |
| value | [string](#string) | optional | Actual string data/URL |
| area | [double](#double) | optional | Area covered by the string data in sq meters |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| version | [Version](#version) | optional | Schema version |

**Example:**
```python
from datatypes import String

string_data = String(
    name="model_name",
    value="my-model-v1"
)
```

### Number
Number represents numeric data types


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.number |
| type | [string](#string) | optional | Type of the number data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the number data |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [Number.MetadataEntry](#number.metadataentry) | repeated | Additional metadata key-value pairs |
| default | [string](#string) | optional | Default value if any |
| value | [string](#string) | optional | Actual number data/URL |
| area | [double](#double) | optional | Area covered by the number data in sq meters |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| version | [Version](#version) | optional | Schema version |

**Example:**
```python
from datatypes import Number

number_data = Number(
    name="threshold",
    value="0.75"
)
```

### Date
Date represents date/time data


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.date |
| type | [string](#string) | optional | Type of the date data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the date data |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [Date.MetadataEntry](#date.metadataentry) | repeated | Additional metadata key-value pairs |
| default | [string](#string) | optional | Default value if any |
| value | [string](#string) | optional | Actual date data/URL |
| area | [double](#double) | optional | Area covered by the date data in sq meters |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| properties | [DateProperties](#dateproperties) | optional | Date-specific properties |
| version | [Version](#version) | optional | Schema version |

**Example:**
```python
from datatypes import Date

date_data = Date(
    name="acquisition_date",
    value="2024-01-01T00:00:00Z"
)
```

### Primary Type Specs
* [DateSpec](#datespec)

* [NumberSpec](#numberspec)

* [RasterSpec](#rasterspec)

* [StringSpec](#stringspec)

* [TabularSpec](#tabularspec)

* [VectorSpec](#vectorspec)

### Properties

* [DateProperties](#dateproperties)

* [RasterProperties](#rasterproperties)

* [TabularProperties](#tabularproperties)

* [VectorProperties](#vectorproperties)

### Validations

* [DateValidation](#datevalidation)

* [NumberValidation](#numbervalidation)

* [RasterValidation](#rastervalidation)

* [StringValidation](#stringvalidation)

* [TabularValidation](#tabularvalidation)

* [VectorValidation](#vectorvalidation)

### Supporting Types

* [Format](#format)

* [Version](#version)

* [VizTypes](#viztypes)

* [AssetSource](#assetsource)

* [Bucket](#bucket)

* [BucketViz](#bucketviz)

* [ContinuousViz](#continuousviz)

* [Date.MetadataEntry](#date.metadataentry)

* [DateSpec.MetadataEntry](#datespec.metadataentry)

* [Discretization](#discretization)

* [DiscretizationClass](#discretizationclass)

* [ListOfBuckets](#listofbuckets)

* [ListOfFloats](#listoffloats)

* [Number.MetadataEntry](#number.metadataentry)

* [NumberSpec.MetadataEntry](#numberspec.metadataentry)

* [Range](#range)

* [Raster.MetadataEntry](#raster.metadataentry)

* [RasterSpec.MetadataEntry](#rasterspec.metadataentry)

* [String.MetadataEntry](#string.metadataentry)

* [StringSpec.MetadataEntry](#stringspec.metadataentry)

* [Tabular.MetadataEntry](#tabular.metadataentry)

* [TabularFileSchema](#tabularfileschema)

* [TabularSpec.MetadataEntry](#tabularspec.metadataentry)

* [Vector.MetadataEntry](#vector.metadataentry)

* [VectorSpec.MetadataEntry](#vectorspec.metadataentry)

* [Visualization](#visualization)

* [Visualization.DiscreteEntry](#visualization.discreteentry)



<a name="datespec"></a>
#### DateSpec
DateSpec defines validation rules for Date type


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.date |
| type | [string](#string) | optional | Type of the date data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the date data |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [DateSpec.MetadataEntry](#datespec.metadataentry) | repeated | Additional metadata key-value pairs |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| properties | [DateProperties](#dateproperties) | optional | Date-specific properties |
| validation | [DateValidation](#datevalidation) | optional | Validation rules |
| version | [Version](#version) | optional | Schema version |


<a name="numberspec"></a>
#### NumberSpec
NumberSpec defines validation rules for Number type


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.number |
| type | [string](#string) | optional | Type of the number data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the number data |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [NumberSpec.MetadataEntry](#numberspec.metadataentry) | repeated | Additional metadata key-value pairs |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| validation | [NumberValidation](#numbervalidation) | optional | Validation rules |
| version | [Version](#version) | optional | Schema version |


<a name="rasterspec"></a>
#### RasterSpec
RasterSpec defines validation rules for Raster type


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.raster |
| type | [string](#string) | optional | Type of the raster data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the raster |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [RasterSpec.MetadataEntry](#rasterspec.metadataentry) | repeated | Additional metadata key-value pairs |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| properties | [RasterProperties](#rasterproperties) | optional | Raster-specific properties |
| validation | [RasterValidation](#rastervalidation) | optional | Validation rules |
| version | [Version](#version) | optional | Schema version |


<a name="stringspec"></a>
#### StringSpec
StringSpec defines validation rules for String type


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.string |
| type | [string](#string) | optional | Type of the string data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the string data |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [StringSpec.MetadataEntry](#stringspec.metadataentry) | repeated | Additional metadata key-value pairs |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| validation | [StringValidation](#stringvalidation) | optional | Validation rules |
| version | [Version](#version) | optional | Schema version |


<a name="tabularspec"></a>
#### TabularSpec
TabularSpec defines validation rules for Tabular type


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.tabular |
| type | [string](#string) | optional | Type of the tabular data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the tabular data |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [TabularSpec.MetadataEntry](#tabularspec.metadataentry) | repeated | Additional metadata key-value pairs |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| properties | [TabularProperties](#tabularproperties) | optional | Tabular-specific properties |
| validation | [TabularValidation](#tabularvalidation) | optional | Validation rules |
| version | [Version](#version) | optional | Schema version |


<a name="vectorspec"></a>
#### VectorSpec
VectorSpec defines validation rules for Vector type


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| format | [Format](#format) | optional | Must be Format.vector |
| type | [string](#string) | optional | Type of the vector data (e.g. "url") |
| name | [string](#string) | optional | Unique identifier for the vector |
| description | [string](#string) | optional | Human readable description |
| display_name | [string](#string) | optional | Name to display in UIs |
| is_artifact | [bool](#bool) | optional | Whether this is a generated artifact |
| group | [string](#string) | optional | Grouping identifier |
| metadata | [VectorSpec.MetadataEntry](#vectorspec.metadataentry) | repeated | Additional metadata key-value pairs |
| asset_source | [AssetSource](#assetsource) | optional | Source information |
| properties | [VectorProperties](#vectorproperties) | optional | Vector-specific properties |
| validation | [VectorValidation](#vectorvalidation) | optional | Validation rules |
| version | [Version](#version) | optional | Schema version |


## Properties

<a name="dateproperties"></a>
#### DateProperties
DateProperties defines properties specific to date data


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| from_aoi | [bool](#bool) | optional | Whether to derive date from AOI |


<a name="rasterproperties"></a>
#### RasterProperties
RasterProperties defines properties specific to raster data


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| bands | [string](#string) | repeated | List of band names in order |
| source | [string](#string) | optional | Original provider of the tiles (e.g. "planetary", "pixxel") |
| collection | [string](#string) | optional | Satellite collection name |
| dtype | [string](#string) | optional | Data type of pixel values |
| satellite_look_angle | [double](#double) | optional | Satellite look angle in degrees |
| sun_elevation | [double](#double) | optional | Sun elevation angle in degrees |
| visualisation | [Visualization](#visualization) | optional | Visualization properties |
| date | [string](#string) | optional | Date of the raster |
| discretization | [Discretization](#discretization) | optional | Discretization properties |
| images | [string](#string) | repeated | STAC URLs of source images |

<a name="tabularproperties"></a>
#### TabularProperties
TabularProperties defines properties specific to tabular data


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| file_type | [string](#string) | optional | File type (e.g. "csv") |
| file_schema | [TabularFileSchema](#tabularfileschema) | optional | Schema definition for the table |


<a name="vectorproperties"></a>
#### VectorProperties
VectorProperties defines properties specific to vector data


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| geometry | [string](#string) | optional | Geometry type of the vector (e.g. "Point", "Polygon") |


## Validations

<a name="datevalidation"></a>
#### DateValidation
DateValidation defines validation rules for dates

Currently no validation fields

<a name="numbervalidation"></a>
#### NumberValidation
NumberValidation defines validation rules for numbers


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| min_value | [double](#double) | optional | Minimum allowed value |
| max_value | [double](#double) | optional | Maximum allowed value |


<a name="rastervalidation"></a>
#### RasterValidation
RasterValidation defines area validation rules for rasters


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| min_area | [double](#double) | optional | Minimum allowed area in square meters |
| max_area | [double](#double) | optional | Maximum allowed area in square meters |

<a name="stringvalidation"></a>
#### StringValidation
StringValidation defines validation rules for strings


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| regex_match | [string](#string) | optional | Regular expression pattern to validate string values |

<a name="tabularvalidation"></a>
#### TabularValidation
TabularValidation defines validation rules for tabular data

Currently no validation fields

<a name="vectorvalidation"></a>
#### VectorValidation
VectorValidation defines area validation rules for vectors


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| min_area | [double](#double) | optional | Minimum allowed area in square meters |
| max_area | [double](#double) | optional | Maximum allowed area in square meters |


## Supporting Types

<a name="format"></a>
#### Format
Format represents the data type format

| Name | Number | Description |
| ---- | ------ | ----------- |
| raster | 0 | For TIFF and GeoTIFF files |
| vector | 1 | For GeoJSON files |
| tabular | 2 | For table-based data like CSV |
| string | 3 | For string values |
| number | 4 | For numeric values |
| date | 5 | For date values |

<a name="version"></a>
#### Version
Version enum represents schema versions

| Name | Number | Description |
| ---- | ------ | ----------- |
| v2 | 0 |  |

<a name="viztypes"></a>
#### VizTypes
VizTypes represents the types of visualizations supported

| Name | Number | Description |
| ---- | ------ | ----------- |
| continuous | 0 | For continuous color gradient visualization |
| bucket | 1 | For histogram-based visualization |
| discrete | 2 | For discrete class-based visualization |

<a name="assetsource"></a>
#### AssetSource
AssetSource defines the source information for an asset


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| id | [string](#string) | optional | Unique identifier for the asset source |
| type | [string](#string) | optional | Type of the asset source (e.g. "internal", "external") |
| identifier | [string](#string) | optional | Human readable identifier |

<a name="bucket"></a>
#### Bucket
Bucket defines a single histogram bucket with color and range


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| color_code | [string](#string) | required | Color code in hex format for this bucket |
| min | [float](#float) | required | Minimum value for this bucket |
| max | [float](#float) | required | Maximum value for this bucket |

<a name="bucketviz"></a>
#### BucketViz
BucketViz defines bucket-based visualization properties


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| bandwise | [ListOfBuckets](#listofbuckets) | repeated | List of bucket definitions per band |


<a name="continuousviz"></a>
#### ContinuousViz
ContinuousViz defines continuous visualization properties


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| color_map_name | [string](#string) | required | Name of the colormap to use from supported colormaps |
| bandwise_range | [Range](#range) | repeated | Range of values per band in a list format, where each item is the range for that band index |


<a name="date.metadataentry"></a>
#### Date.MetadataEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |

<a name="datespec.metadataentry"></a>
#### DateSpec.MetadataEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |

<a name="discretization"></a>
#### Discretization
Discretization defines how continuous data is discretized


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| type | [string](#string) | optional | Type of discretization - "interval" or "index" |
| classes | [DiscretizationClass](#discretizationclass) | repeated | List of class definitions |


<a name="discretizationclass"></a>
#### DiscretizationClass
DiscretizationClass represents a single class in discretized distribution


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| color | [string](#string) | optional | Color code in hex format |
| name | [string](#string) | optional | Name of the class |
| value | [string](#string) | optional | Value representing the class for index-based discretization |
| range | [Range](#range) | optional | Range representing the class for interval-based discretization |


<a name="listofbuckets"></a>
#### ListOfBuckets
ListOfBuckets represents a list of histogram buckets


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| items | [Bucket](#bucket) | repeated |  |


<a name="listoffloats"></a>
#### ListOfFloats
ListOfFloats represents a list of float values


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| values | [float](#float) | repeated |  |


<a name="number.metadataentry"></a>
#### Number.MetadataEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |


<a name="numberspec.metadataentry"></a>
#### NumberSpec.MetadataEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |


<a name="range"></a>
#### Range
Range represents a min-max numerical range


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| min | [float](#float) | required |  |
| max | [float](#float) | required |  |



<a name="raster.metadataentry"></a>
#### Raster.MetadataEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |


<a name="rasterspec.metadataentry"></a>
#### RasterSpec.MetadataEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |


<a name="string.metadataentry"></a>
#### String.MetadataEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |


<a name="stringspec.metadataentry"></a>
#### StringSpec.MetadataEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |


<a name="tabular.metadataentry"></a>
#### Tabular.MetadataEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |



<a name="tabularfileschema"></a>
#### TabularFileSchema
TabularFileSchema defines the schema for tabular data


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| headers | [string](#string) | repeated | Ordered list of column headers |


<a name="tabularspec.metadataentry"></a>
#### TabularSpec.MetadataEntry


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |


<a name="vector.metadataentry"></a>
#### Vector.MetadataEntry


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |
\
<a name="vectorspec.metadataentry"></a>
#### VectorSpec.MetadataEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |


<a name="visualization"></a>
#### Visualization
Visualization defines the visualization properties for a raster


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| type | [VizTypes](#viztypes) | optional | Type of visualization (continuous, bucket or discrete) |
| continuous | [ContinuousViz](#continuousviz) | optional | Properties for continuous visualization |
| bucket | [BucketViz](#bucketviz) | optional | Properties for histogram based bucket visualization |
| discrete | [Visualization.DiscreteEntry](#visualization.discreteentry) | repeated | Mapping of pixel values to colors for discrete visualization |






<a name="visualization.discreteentry"></a>
#### Visualization.DiscreteEntry



| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| key | [string](#string) | optional |  |
| value | [string](#string) | optional |  |







## Scalar Value Types

| .proto Type | Notes | C++ Type | Java Type | Python Type |
| ----------- | ----- | -------- | --------- | ----------- |
| double | | double | double | float |
| float | | float | float | float |
| int32 | Uses variable-length encoding | int32 | int | int |
| int64 | Uses variable-length encoding | int64 | long | int/long |
| uint32 | Uses variable-length encoding | uint32 | int | int/long |
| uint64 | Uses variable-length encoding | uint64 | long | int/long |
| sint32 | Uses variable-length encoding | int32 | int | int |
| sint64 | Uses variable-length encoding | int64 | long | int/long |
| fixed32 | Always four bytes | uint32 | int | int |
| fixed64 | Always eight bytes | uint64 | long | int/long |
| sfixed32 | Always four bytes | int32 | int | int |
| sfixed64 | Always eight bytes | int64 | long | int/long |
| bool | | bool | boolean | boolean |
| string | | string | String | str/unicode |
| bytes | | string | ByteString | str |

## Installation

The datatypes package is inherently included in clay but can also be installed separately:

```bash
# Python
pip install pixxel-datatypes

# Go (imported as module)
import "github.com/example/clay/proto/go"
```