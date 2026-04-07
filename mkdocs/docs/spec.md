# Block Specification

The block specification file (`clay.yaml`) defines your block's metadata, inputs, outputs, and build configuration. This file is required for Clay to understand how to build, deploy, and run your block.

## Example Specification

```yaml
apiVersion: 0.0.1
kind: block
type: processing
name: myblock
version: v0.0.1
author: your-name
tags:
  - imagery
  - processing

parameters:
  - name: weight
    type: int
    default: 5

inputs:
   - name: ndvi_raster
    format: raster
    is_artifact: true
    type: url
    version: v2
    validation:
      min_area: 10
    properties:
      source: planetary
      collection: sentinel-2-l2a

  - name: input1
    format: string
    type: str

  - name: input2
    format: number
    type: int

outputs:
  - name: output1
    format: number
    type: int

build:
  python-version: "3.10"
  conda: false
  gdal: true
  apt-get:
    - wget
  requirements: requirements.txt

gpu: false

env:
  SAMPLE_ENV: "sample"
```

---

## Field Reference

### apiVersion

| | |
|---|---|
| **Key** | `apiVersion` |
| **Type** | `string` |
| **Required** | Yes |

The API version of the specification format. Currently `0.0.1`.

---

### kind

| | |
|---|---|
| **Key** | `kind` |
| **Type** | `string` |
| **Required** | Yes |

Specifies what kind of entity this spec file represents. For blocks, this should always be `block`.

---

### type

| | |
|---|---|
| **Key** | `type` |
| **Type** | `string` |
| **Required** | Yes |
| **Values** | `processing`, `source` |

Type of the block:

- **`processing`**: Blocks that perform analysis, predictions, or transformations on input data
- **`source`**: Blocks that generate or fetch data without requiring input data

For more information, see [FAQ: Difference between processing and source blocks](faq.md#difference-between-processing-and-source-blocks).

---

### name

| | |
|---|---|
| **Key** | `name` |
| **Type** | `string` |
| **Required** | Yes |

A unique identifier for the block. Must contain only **lowercase** alphanumeric characters and hyphens.

!!! warning
    Once the `name` is set for a block, it cannot be changed. All subsequent versions must use the same name.

---

### version

| | |
|---|---|
| **Key** | `version` |
| **Type** | `string` |
| **Required** | Yes |

Version of the block following [semantic versioning](https://semver.org/) (e.g., `v0.0.1`, `v1.2.3`).

!!! tip "Recommendation"
    Version your blocks as you would software releases. Increment the version when making changes to inputs, outputs, or block behavior.

---

### author

| | |
|---|---|
| **Key** | `author` |
| **Type** | `string` |
| **Required** | Yes |

The individual or team responsible for maintaining this block.

---

### tags

| | |
|---|---|
| **Key** | `tags` |
| **Type** | `list[string]` |
| **Required** | No |

A list of tags for categorizing and discovering the block.

```yaml
tags:
  - imagery
  - processing
  - ndvi
  - vegetation
```

---

### parameters

| | |
|---|---|
| **Key** | `parameters` |
| **Type** | `list[parameter]` |
| **Required** | No |

List of parameters passed to the block's `setup()` function during initialization. These are configuration values that remain constant during block execution.

#### Parameter Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Parameter name (must match the argument name in `setup()`) |
| `type` | string | Data type: `str`, `int`, `float`, `bool`, `list`, `dict` |
| `default` | any | Default value if not provided at runtime |

**Example:**
```yaml
parameters:
  - name: threshold
    type: float
    default: 0.5

  - name: bands
    type: list
    default:
      - B04
      - B08
```

---

### inputs

| | |
|---|---|
| **Key** | `inputs` |
| **Type** | `list[input]` |
| **Required** | Yes |

List of inputs the block accepts. Each input must specify its format and type. See [Input/Output & Datatypes](IO.md) for supported formats.

!!! note
    Do not include the `value` field in the specification. The spec defines *what* inputs the block accepts, not the actual values.

#### Input Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Input name (must match the parameter name in `preprocess()`) |
| `format` | string | Yes | Data format: `raster`, `vector`, `tabular`, `string`, `number`, `date` |
| `type` | string | Yes | Value type: `url`, `str`, `int`, `float`, `bool` |
| `description` | string | No | Human-readable description |
| `display_name` | string | No | Display name for UIs |
| `is_artifact` | bool | No | Whether this is a file artifact (default: true for raster/vector) |
| `properties` | object | No | Format-specific properties |
| `validation` | object | No | Validation rules |

**Example:**
```yaml
inputs:
  - name: satellite_image
    format: raster
    type: url
    description: Input satellite imagery
    properties:
      collection: sentinel-2
    validation:
      min_area: 10
      max_area: 1000

  - name: threshold
    format: number
    type: float
    validation:
      min_value: 0.0
      max_value: 1.0

  - name: aoi
    format: vector
    type: url
    properties:
      geometry: Polygon
```

---

### outputs

| | |
|---|---|
| **Key** | `outputs` |
| **Type** | `list[output]` |
| **Required** | Yes |

List of outputs the block produces. Each output must specify its format and type.

!!! note
    Do not include the `value` field in the specification. The spec defines *what* outputs the block produces, not the actual values.

#### Output Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Output name (must match the key returned from `postprocess()`) |
| `format` | string | Yes | Data format: `raster`, `vector`, `tabular`, `string`, `number`, `date` |
| `type` | string | Yes | Value type: `url`, `str`, `int`, `float`, `bool` |
| `description` | string | No | Human-readable description |
| `display_name` | string | No | Display name for UIs |
| `is_artifact` | bool | No | Whether this is a file artifact |
| `properties` | object | No | Format-specific properties |

**Example:**
```yaml
outputs:
  - name: result
    format: raster
    type: url
    description: Processed output raster
    properties:
      dtype: float32

  - name: statistics
    format: tabular
    type: url

  - name: confidence
    format: number
    type: float
```

---

### build

| | |
|---|---|
| **Key** | `build` |
| **Type** | `object` |
| **Required** | Yes |

Build-time configuration for the Docker image.

#### Build Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `python-version` | string | `"3.10"` | Python version for the Docker image |
| `conda` | bool | `false` | Use conda as the environment manager |
| `gdal` | bool | `false` | Install GDAL at the OS level |
| `apt-get` | list[string] | `[]` | Additional OS packages to install |
| `requirements` | string | - | Path to requirements.txt or conda.yaml |

**Example:**
```yaml
build:
  python-version: "3.10"
  conda: false
  gdal: true
  apt-get:
    - wget
    - libgl1-mesa-glx
  requirements: requirements.txt
```

!!! tip
    If your block requires geospatial libraries like `rasterio` or `geopandas`, set `gdal: true` to ensure GDAL is available.

---

### gpu

| | |
|---|---|
| **Key** | `gpu` |
| **Type** | `bool` |
| **Default** | `false` |

Whether the block requires GPU acceleration. When set to `true`, the block will be scheduled on GPU-enabled infrastructure.

```yaml
gpu: true
```

---

### env

| | |
|---|---|
| **Key** | `env` |
| **Type** | `object` |
| **Required** | No |

Environment variables to set in the container at runtime.

```yaml
env:
  MODEL_CACHE_DIR: "/tmp/cache"
  LOG_LEVEL: "INFO"
```

!!! warning
    Do not store sensitive values (API keys, passwords) directly in the spec file. Use secrets management instead.

---

## Validation Rules

Clay supports input validation to ensure data meets requirements before processing. Add a `validation` field to any input.

### Number Validation

```yaml
inputs:
  - name: threshold
    format: number
    type: float
    validation:
      min_value: 0.0
      max_value: 1.0
```

### Number Allowed Values

```yaml
inputs:
  - name: zoom_level
    format: number
    type: int
    validation:
      allowed_values:
        - 10
        - 12
        - 14
        - 16
```

### String Validation

```yaml
inputs:
  - name: uuid
    format: string
    type: str
    validation:
      regex_match: '[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-...'
```

### String Allowed Values

```yaml
inputs:
  - name: classification_type
    format: string
    type: str
    validation:
      allowed_values:
        - "urban"
        - "forest"
        - "water"
        - "agriculture"
```

### Area Validation (Raster/Vector)

```yaml
inputs:
  - name: image
    format: raster
    type: url
    validation:
      min_area: 10    # sq km
      max_area: 1000  # sq km
```

---

## Complete Example

Here's a complete specification for an NDVI block:

```yaml
apiVersion: 0.0.1
kind: block
type: processing
name: ndvi-calculator
version: v1.0.0
author: ml-team
tags:
  - vegetation
  - ndvi
  - satellite

parameters:
  - name: bands
    type: list
    default:
      - B04
      - B08

inputs:
  - name: satellite_image
    format: raster
    type: url
    description: Sentinel-2 or similar multispectral imagery
    properties:
      collection: sentinel-2
    validation:
      min_area: 1
      max_area: 500

outputs:
  - name: ndvi_result
    format: raster
    type: url
    description: NDVI values ranging from -1 to 1
    properties:
      dtype: float32

build:
  python-version: "3.10"
  gdal: true
  conda: false
  apt-get:
    - wget
  requirements: requirements.txt

gpu: false

env:
  GDAL_CACHEMAX: "512"
```
