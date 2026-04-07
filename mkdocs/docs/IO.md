# Input/Output & Datatypes

An ML block can be considered as a black box function that takes something as input and returns something which is treated as output. Clay enforces the block to have input and output of certain `types`. We call these types `datatypes`.

## Why do we need Types?

You might be wondering, *why do we even need types? What is this additional layer of complexity? Why should I learn one more thing?* The answer boils down to this:

> For blocks to work together and with each other, they need to speak the same language.

Since blocks are developed in silos and as independent entities, *but* are expected to work with each other in connected chains, they need to have a common *dialect* that they and the broader system understands. Using this *dialect*, the blocks specify their *inputs* and their *outputs*. Since all blocks and the system speak the same language, they can determine whether the output of one block can be compatible with the input of another block.

For example, if `BlockA` outputs a `GeoTiff` file and `BlockB` accepts a `GeoJSON` as input, the output of `BlockA` cannot be provided as input to `BlockB`, because they are of different `Types`.

![types-1](assets/types-1.png)

But this works:

![types-2](assets/types-2.png)

## Supported Types

| Type | Description | Common Use Case |
|------|-------------|-----------------|
| **Raster** | GeoTIFF/TIFF data | Satellite imagery, elevation data |
| **Vector** | GeoJSON data | Boundaries, points of interest |
| **Tabular** | CSV/table data | Statistics, reports |
| **Number** | Numeric values | Thresholds, parameters |
| **String** | Text values | Block names, identifiers |
| **Date** | Date/time values | Acquisition dates, timestamps |

All types are available through the `datatypes` module:

```python
import datatypes

# Access types as datatypes.Raster, datatypes.Vector, etc.
```

## Common Attributes

All datatypes share these common attributes:

| Attribute | Required | Description |
|-----------|----------|-------------|
| `format` | Yes | The data format (raster, vector, tabular, string, number, date) |
| `type` | Yes | The data type of the value (url, string, int, float, bool, list, dict) |
| `name` | Yes | Unique identifier that matches the parameter name in your block |
| `value` | Yes | The actual data or URL to the data |
| `description` | No | Human readable description |
| `display_name` | No | Name to display in UIs |
| `is_artifact` | No | Whether this is a generated artifact |
| `properties` | No | Format-specific metadata |
| `metadata` | No | Additional key-value pairs |

??? abstract "Disambiguation between `format` and `type`"

    **Format** is a high-level entity that has conceptual meaning, which may or may not have meaning in programming languages. For example, raster/vectors etc.

    **Type** is an actual data type (like string, number, float) that means something in general programming languages. It's technically the dtype of the `value` parameter and tells the consumer how to interact with the value attribute.

---

## Fundamental Types

### Raster

Raster represents TIFF/GeoTIFF data, commonly used for satellite imagery and geospatial raster data.

| Field | Type | Description |
|-------|------|-------------|
| `format` | Format | Must be `raster` |
| `type` | string | Type of the raster data (e.g., "url") |
| `name` | string | Unique identifier for the raster |
| `value` | string | Actual raster data/URL |
| `description` | string | Human readable description |
| `display_name` | string | Name to display in UIs |
| `is_artifact` | bool | Whether this is a generated artifact (default: true) |
| `properties` | [RasterProperties](#rasterproperties) | Raster-specific properties |
| `stac_url` | string | STAC item URL |
| `area` | double | Area covered in square meters |

**Example:**
```python
import datatypes

raster_input = datatypes.Raster(
    name="input_image",
    type="url",
    value="s3://bucket/path/to/image.tif",
    properties=datatypes.RasterProperties(
        bands=["B02", "B03", "B04"],
        collection="sentinel-2"
    )
)

# Access the value
image_path = raster_input.value
```

---

### Vector

Vector represents GeoJSON data, used for polygons, points, and other geometric data.

| Field | Type | Description |
|-------|------|-------------|
| `format` | Format | Must be `vector` |
| `type` | string | Type of the vector data (e.g., "url") |
| `name` | string | Unique identifier for the vector |
| `value` | string | Actual vector data/URL |
| `description` | string | Human readable description |
| `display_name` | string | Name to display in UIs |
| `is_artifact` | bool | Whether this is a generated artifact (default: true) |
| `properties` | [VectorProperties](#vectorproperties) | Vector-specific properties |
| `area` | double | Area covered in square meters |

**Example:**
```python
import datatypes

boundary = datatypes.Vector(
    name="aoi",
    type="url",
    value="s3://bucket/path/to/boundary.geojson",
    properties=datatypes.VectorProperties(geometry="Polygon")
)
```

---

### Tabular

Tabular represents table-based data like CSV files.

| Field | Type | Description |
|-------|------|-------------|
| `format` | Format | Must be `tabular` |
| `type` | string | Type of the tabular data (e.g., "url") |
| `name` | string | Unique identifier for the tabular data |
| `value` | string | Actual tabular data/URL |
| `description` | string | Human readable description |
| `display_name` | string | Name to display in UIs |
| `is_artifact` | bool | Whether this is a generated artifact (default: true) |
| `properties` | [TabularProperties](#tabularproperties) | Tabular-specific properties |

**Example:**
```python
import datatypes

results = datatypes.Tabular(
    name="analysis_results",
    type="url",
    value="s3://bucket/path/to/results.csv"
)
```

---

### Number

Number represents numeric data types (integers, floats).

| Field | Type | Description |
|-------|------|-------------|
| `format` | Format | Must be `number` |
| `type` | string | Type (e.g., "int", "float") |
| `name` | string | Unique identifier |
| `value` | string | The numeric value (as string) |
| `description` | string | Human readable description |
| `display_name` | string | Name to display in UIs |
| `is_artifact` | bool | Whether this is a generated artifact (default: false) |

**Example:**
```python
import datatypes

threshold = datatypes.Number(
    name="confidence_threshold",
    type="float",
    value="0.75"
)

# Access the value
print(f"Threshold: {threshold.value}")
```

---

### String

String represents text data.

| Field | Type | Description |
|-------|------|-------------|
| `format` | Format | Must be `string` |
| `type` | string | Type (e.g., "str") |
| `name` | string | Unique identifier |
| `value` | string | The string value |
| `description` | string | Human readable description |
| `display_name` | string | Name to display in UIs |
| `is_artifact` | bool | Whether this is a generated artifact (default: false) |

**Example:**
```python
import datatypes

block_name = datatypes.String(
    name="block_version",
    value="v1.2.0"
)
```

---

### Date

Date represents date/time data.

| Field | Type | Description |
|-------|------|-------------|
| `format` | Format | Must be `date` |
| `type` | string | Type (e.g., "str") |
| `name` | string | Unique identifier |
| `value` | string | The date value (ISO 8601 format) |
| `description` | string | Human readable description |
| `display_name` | string | Name to display in UIs |
| `is_artifact` | bool | Whether this is a generated artifact (default: false) |
| `properties` | [DateProperties](#dateproperties) | Date-specific properties |

**Example:**
```python
import datatypes

acquisition_date = datatypes.Date(
    name="image_date",
    value="2024-01-15T00:00:00Z"
)
```

---

## Type Properties

### RasterProperties

Properties specific to raster data:

| Field | Type | Description |
|-------|------|-------------|
| `bands` | list[string] | List of band names in order |
| `source` | string | Original provider (e.g., "planetary") |
| `collection` | string | Satellite collection name |
| `dtype` | string | Data type of pixel values |
| `satellite_look_angle` | double | Satellite look angle in degrees |
| `sun_elevation` | double | Sun elevation angle in degrees |
| `visualisation` | [Visualization](#visualization) | Visualization properties |
| `discretization` | [Discretization](#discretization) | Discretization properties |
| `images` | list[string] | STAC URLs of source images |

### VectorProperties

| Field | Type | Description |
|-------|------|-------------|
| `geometry` | string | Geometry type (e.g., "Point", "Polygon", "MultiPolygon") |

### TabularProperties

| Field | Type | Description |
|-------|------|-------------|
| `file_type` | string | File type (e.g., "csv") |
| `file_schema` | [TabularFileSchema](#tabularfileschema) | Schema definition for the table |

### TabularFileSchema

| Field | Type | Description |
|-------|------|-------------|
| `headers` | list[string] | Ordered list of column headers |

**Example:**
```python
import datatypes

results = datatypes.Tabular(
    name="analysis_results",
    type="url",
    value="s3://bucket/path/to/results.csv",
    properties=datatypes.TabularProperties(
        file_type="csv",
        file_schema=datatypes.TabularFileSchema(
            headers=["id", "latitude", "longitude", "value", "timestamp"]
        )
    )
)
```

### DateProperties

| Field | Type | Description |
|-------|------|-------------|
| `from_aoi` | bool | Whether to derive date from AOI |

---

## Input Validations

Clay supports validating input values in your block specification. Validations are defined in the `validation` field of each input.

### Number Validation

Check if a number is within a specified range:

```yaml
inputs:
  - name: threshold
    format: number
    type: float
    validation:
      min_value: 0.0
      max_value: 1.0
```

### String Validation

Validate string values against a regular expression:

```yaml
inputs:
  - name: uuid_input
    format: string
    type: str
    validation:
      regex_match: '[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'
```

### Raster Validation

Validate the area of the raster's AOI (in square kilometers):

```yaml
inputs:
  - name: satellite_image
    format: raster
    type: url
    validation:
      min_area: 10    # minimum 10 sq km
      max_area: 1000  # maximum 1000 sq km
```

### Vector Validation

Validate the area of the vector's AOI (in square kilometers):

```yaml
inputs:
  - name: boundary
    format: vector
    type: url
    validation:
      min_area: 1
      max_area: 500
```

---

## Visualization

Raster outputs can include visualization properties for rendering on maps.

### Continuous Visualization

For continuous color gradients:

```python
import datatypes

output = datatypes.Raster(
    name="ndvi_result",
    value="result.tif",
    properties=datatypes.RasterProperties(
        visualisation=datatypes.Visualization(
            type="continuous",
            continuous=datatypes.ContinuousViz(
                color_map_name="viridis",
                bandwise_range=[datatypes.Range(min=-1.0, max=1.0)]
            )
        )
    )
)
```

### Bucket Visualization

For histogram-based visualization with defined buckets:

```python
import datatypes

viz = datatypes.Visualization(
    type="bucket",
    bucket=datatypes.BucketViz(
        bandwise=[
            datatypes.ListOfBuckets(items=[
                datatypes.Bucket(color_code="#ff0000", min=0.0, max=0.3),
                datatypes.Bucket(color_code="#ffff00", min=0.3, max=0.6),
                datatypes.Bucket(color_code="#00ff00", min=0.6, max=1.0)
            ])
        ]
    )
)
```

### Discrete Visualization

For categorical/classified data:

```python
import datatypes

viz = datatypes.Visualization(
    type="discrete",
    discrete={"1": "#ff0000", "2": "#00ff00", "3": "#0000ff"}
)
```

---

## Discretization

For rasters that represent classified data:

```python
import datatypes

properties = datatypes.RasterProperties(
    discretization=datatypes.Discretization(
        type="interval",
        classes=[
            datatypes.DiscretizationClass(name="Low", color="#ff0000", range=datatypes.Range(min=0, max=0.3)),
            datatypes.DiscretizationClass(name="Medium", color="#ffff00", range=datatypes.Range(min=0.3, max=0.7)),
            datatypes.DiscretizationClass(name="High", color="#00ff00", range=datatypes.Range(min=0.7, max=1.0))
        ]
    )
)
```

---

## Usage in Blocks

Here's how to use datatypes in your Clay block:

```python
from clay.core import BlockWrapper
import datatypes

class MyBlock(BlockWrapper):
    async def preprocess(self, input_raster: datatypes.Raster, threshold: datatypes.Number):
        # Access values using .value attribute
        self.logger.info(f"Processing raster: {input_raster.value}")
        self.logger.info(f"Using threshold: {threshold.value}")

        return {
            "raster_path": input_raster.value,
            "threshold_value": float(threshold.value)
        }

    async def postprocess(self, result_path: str):
        # Return outputs as datatypes
        return {
            "output": datatypes.Raster(
                name="result",
                value=result_path,
                is_artifact=True
            )
        }
```

!!! tip "Accessing Values"
    Always use the `.value` attribute (lowercase) to access the actual data from a datatype object.
