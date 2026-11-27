---
title: Block Specification
order: 5
---

# Block Specification

The block specification file (`clay.yaml`) defines your block's metadata, inputs, outputs, and build configuration. This file is required for Clay to understand how to build, deploy, and run your block.

## Example Specification

```yaml
# yaml-language-server: $schema=https://pixxelhq.github.io/clay/schema/v1.json
apiVersion: clay/v1
kind: block
type: processing
name: myblock
version: 0.0.1
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

## Schema and editor support

The `clay/v1` format has a [JSON Schema](https://json-schema.org/) at
`https://pixxelhq.github.io/clay/schema/v1.json`.

`clay new` and `clay init` write this as the first line of `clay.yaml`:

```yaml
# yaml-language-server: $schema=https://pixxelhq.github.io/clay/schema/v1.json
```

Editors that use the YAML language server read this line and then complete
keys and values, show the description of each key, and mark errors as you
type. In VS Code, install the
[YAML extension by Red Hat](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml).
To use the schema in an older `clay.yaml`, add the line and change
`apiVersion` to `clay/v1`.

Every Clay command that reads `clay.yaml` checks the file against the schema
of its `apiVersion` and lists each problem, for example:

```text
error: clay.yaml does not match the clay/v1 schema:
  clay.yaml: additional properties 'title' not allowed
  clay.yaml: inputs[1].format: value must be one of 'raster', 'vector', 'tabular', 'string', 'number', 'date'
  clay.yaml: version: must be a semantic version without a leading v, such as 1.2.3
```

Clay stops if `apiVersion` is missing or is not one that this version of
Clay supports. The only supported value is `clay/v1`.

---

## Moving to clay/v1

A `clay.yaml` made by an older Clay has `apiVersion: 0.0.1` and a version
such as `v0.0.1`. To build or publish it with this version of Clay:

1. Set `apiVersion: clay/v1`, and add the schema line at the top so that your
   editor checks the file:

    ```yaml
    # yaml-language-server: $schema=https://pixxelhq.github.io/clay/schema/v1.json
    apiVersion: clay/v1
    ```

2. Remove the leading `v` from `version`: `v1.2.3` becomes `1.2.3`. The image
   is then tagged `<name>:1.2.3`. The registry already stores versions without
   the `v`, so published versions keep their numbers.
3. Run `clay dockerfile`. It reads `clay.yaml` without Docker and lists every
   key that does not match the schema. Fix each one, or remove keys that Clay
   does not know.

---

## Field Reference

### apiVersion

| | |
|---|---|
| **Key** | `apiVersion` |
| **Type** | `string` |
| **Required** | Yes |

The version of the specification format. Clay checks the file against the [schema](#schema-and-editor-support) of this version, and stops if the version is missing or not supported. The only supported value is `clay/v1`. A `clay.yaml` made by an older Clay has `0.0.1`; see [Moving to clay/v1](#moving-to-clayv1).

---

### kind

| | |
|---|---|
| **Key** | `kind` |
| **Type** | `string` |
| **Required** | Yes |

What the spec file describes. Must be `block`: the registry rejects other values when you run `clay publish`.

---

### type

| | |
|---|---|
| **Key** | `type` |
| **Type** | `string` |
| **Required** | Yes |
| **Values** | `processing`, `source`, `visualization` |

Type of the block:

- **`processing`**: Blocks that perform analysis, predictions, or transformations on input data
- **`source`**: Blocks that generate or fetch data without requiring input data

The registry rejects other values when you run `clay publish`. The CLI and the runtime do not read `type`; Clay builds and runs all block types the same way.

For more information, see [FAQ: Difference between processing and source blocks](faq.md#difference-between-processing-and-source-blocks).

---

### name

| | |
|---|---|
| **Key** | `name` |
| **Type** | `string` |
| **Required** | Yes |

The name of the block. `clay build`, `clay run` and `clay push` use `<name>:<version>` as the Docker image name, and the registry stores the block under this name.

`name` must start with a lowercase letter, end with a lowercase letter or digit, and contain only lowercase letters, digits, `-` and `_`, so it is also a valid Docker image name. Use the form that `clay new` writes, such as `my-block`.

The registry keeps one block per `name`. If you change `name`, `clay publish` creates a new block; the versions published under the old name stay there.

---

### version

| | |
|---|---|
| **Key** | `version` |
| **Type** | `string` |
| **Required** | Yes |

Version of the block, as a [semantic version](https://semver.org/) with all three parts and without a leading `v`, for example `1.2.3` or `1.2.3-rc.1`. Clay rejects `v1.2.3`, `1.2` and build metadata such as `1.2.3+abc`.

The value is the Docker image tag (`<name>:<version>`), and the registry stores the block version under it.

!!! tip "Recommendation"
    Version your blocks as you would software releases. Increment the version when making changes to inputs, outputs, or block behavior.

---

### author

| | |
|---|---|
| **Key** | `author` |
| **Type** | `string` |
| **Required** | Yes |

The individual or team responsible for maintaining this block. Clay checks that it is not empty when it reads `clay.yaml`; the registry requires it too.

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

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Parameter name (must match the argument name in `setup()`) |
| `type` | string | Yes | Data type: `str`, `int`, `float`, `bool`, `list`, `dict`. Clay also accepts `string`, `url` (as `str`), `path` (as a `pathlib.Path`) and `boolean` (as `bool`) |
| `default` | any | Yes | The value passed to `setup()`. Clay converts it to `type` |
| `format` | string | No | Data format: `raster`, `vector`, `tabular`, `string`, `number`, `date`. Clay does not read it |
| `description` | string | No | Human-readable description. Clay does not read it |

Clay always passes `default` to `setup()`. Clay reports a parameter without `name`, `type` or `default` when it reads `clay.yaml`. A block without parameters can leave out `parameters` or leave it empty.

Clay converts `default` with the Python function for `type`. For `bool` this is `bool()`, so write `true` or `false` without quotes: the quoted string `"false"` becomes `True`. `list` and `dict` values are passed as they are, and an unknown `type` is converted with `str()`.

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

List of inputs the block accepts. See [Input/Output & Datatypes](IO.md) for supported formats.

!!! note
    Do not include the `value` field in the specification. The spec defines *what* inputs the block accepts, not the actual values.

#### Input Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Input name (must match the parameter name in `preprocess()`) |
| `format` | string | Yes | Data format: `raster`, `vector`, `tabular`, `string`, `number`, `date` |
| `type` | string | Yes | Value type: `url`, `str`, `int`, `float`, `bool` or `boolean` |
| `description` | string | No | Human-readable description |
| `display_name` | string | No | Display name for UIs |
| `is_artifact` | bool | No | Whether this is a file artifact. Clay does not read this field from `clay.yaml`; it is stored with the spec in the registry. At runtime, the `is_artifact` of the run's input (for inputs) or of the datatype the block returns (for outputs) decides. Default: `true` for `raster`, `vector` and `tabular`; `false` for the others |
| `default` | string | No | Used when the input's `value` is `""`. See the note below |
| `properties` | object | No | Format-specific properties |
| `validation` | object | No | Validation rules — see [Validation Rules](#validation-rules). Clay rejects a rule that does not belong to the input's `format` |
| `group` | string | No | Group name. Clay does not read it; it is stored with the spec in the registry |
| `metadata` | mapping of text to text | No | Free-form metadata. Clay does not read it from `clay.yaml`; it is stored with the spec in the registry |
| `asset_source` | object | No | Where the data comes from: `id`, `type` and `layer_name`, all text. Clay does not read it from `clay.yaml`; it is stored with the spec in the registry |
| `version` | string | No | Version of the datatype format. The only value is `v2`, which is also the default |

!!! note "What the runtime reads"
    At run time, `format`, `type` and `is_artifact` come from the run's input JSON, not from `clay.yaml`. From each input in `clay.yaml`, the runtime reads only `name`, `default` and `validation`.

    `default` applies only to inputs that are in the run's input list. Write it as text: Clay rejects a number such as `default: 5` when it reads `clay.yaml`; write `default: "5"`. For a `raster` input whose run input has no `stac_url`, Clay also sets `stac_url` to `default` and reads it as a STAC JSON file (a local path or an `http(s)` URL), even when `value` is set. If the `default` of a `raster` input is not a STAC item, pass `stac_url` in every run.

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

List of outputs the block produces.

!!! note
    Do not include the `value` field in the specification. The spec defines *what* outputs the block produces, not the actual values.

#### Output Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Output name. Must match the `name` of a datatype that `postprocess()` returns. The keys of the dict that `postprocess()` returns are not used. If the block returns an output whose `name` is not declared here, the run fails with a `KeyError` |
| `format` | string | Yes | Data format: `raster`, `vector`, `tabular`, `string`, `number`, `date` |
| `type` | string | Yes | Value type: `url`, `str`, `int`, `float`, `bool` or `boolean` |
| `description` | string | No | Human-readable description |
| `display_name` | string | No | Display name for UIs |
| `is_artifact` | bool | No | Whether this is a file artifact. Clay does not read this field from `clay.yaml`; it is stored with the spec in the registry. At runtime, the `is_artifact` of the run's input (for inputs) or of the datatype the block returns (for outputs) decides. Default: `true` for `raster`, `vector` and `tabular`; `false` for the others |
| `properties` | object | No | Format-specific properties. Merged into the `properties` of the output that the block returns, except for `string` and `number` outputs. Values set by the block win. A key that is not a property of the format (see [Type Properties](IO.md#type-properties)) makes the run fail |
| `group` | string | No | Group name. Clay does not read it; it is stored with the spec in the registry |
| `metadata` | mapping of text to text | No | Free-form metadata. Clay does not read it from `clay.yaml`; it is stored with the spec in the registry |
| `asset_source` | object | No | Where the data comes from: `id`, `type` and `layer_name`, all text. Clay does not read it from `clay.yaml`; it is stored with the spec in the registry |
| `version` | string | No | Version of the datatype format. The only value is `v2`, which is also the default |

At run time, `format`, `type` and `is_artifact` come from the datatype that the block returns. From each output in `clay.yaml`, the runtime reads only `name` and `properties`.

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

Build-time configuration for the Docker image. Clay uses it only when it generates the Dockerfile: when the project has no `./Dockerfile` and `-f` is not given. With your own Dockerfile, its values are not used, but `clay.yaml` still needs `build`, for example `build: {}`: `clay publish` sends it to the registry, which requires it.

#### Build Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `python-version` | string | `"3.10"` | Python version of the block: `"3.10"`, `"3.11"` or `"3.12"`. Quote the value. YAML reads `3.10` as a number, and Clay stops with `clay.yaml: build.python-version: must be text, not a number` |
| `gdal` | bool | `false` | Install GDAL and its Python bindings (`osgeo`). See [Base image](#base-image) |
| `conda` | bool | `false` | Create a conda environment from the conda file in `requirements`. It does not add CUDA. See [Base image](#base-image) |
| `apt-get` | list[string] | `[]` | Additional OS packages, installed without recommended packages. With `conda: true`, Clay always adds `libgl1`. The `python:<version>-slim` and OSGeo images have no C compiler; add `build-essential` if a package in `requirements` must be compiled |
| `requirements` | string | Required | Path to the `requirements.txt` file, or to the conda file if `conda` is `true`. Clay does not check it. If it is missing or empty, `docker build` fails |

**Example:**
```yaml
build:
  python-version: "3.10"
  gdal: true
  conda: false
  apt-get:
    - wget
    - libgl1
  requirements: requirements.txt
```

#### Base image

Clay chooses the base image from `python-version`, `gdal` and `conda`. All base images have pinned versions.

| `conda` | `gdal` | `python-version` | Base image | Packages from `requirements` |
|---------|--------|------------------|------------|------------------------------|
| `false` | `false` | any | `python:<version>-slim` (Debian) | Installed with `uv pip` |
| `false` | `true` | `"3.10"` | [OSGeo GDAL](https://github.com/OSGeo/gdal/pkgs/container/gdal) `ubuntu-small-3.8.5` (Ubuntu 22.04, GDAL 3.8.5) | Installed with `uv pip`, next to the image's GDAL bindings |
| `false` | `true` | `"3.12"` | OSGeo GDAL `ubuntu-small-3.12.4` (Ubuntu 24.04, GDAL 3.12.4) | Installed with `uv pip`, next to the image's GDAL bindings |
| `false` | `true` | `"3.11"` | None: Clay stops with an error, because there is no OSGeo image with Python 3.11. Set `conda: true` to get GDAL from conda, use `"3.10"` or `"3.12"`, or set `gdal: false` if the block does not import `osgeo` | - |
| `true` | any | any | `mambaorg/micromamba` (Debian 12), without CUDA | Conda environment created from the conda file, with `python=<python-version>`, and `gdal` if `gdal` is `true` |

!!! tip
    Set `gdal: true` only if your block imports `osgeo`. The `rasterio`, `fiona` and `pyogrio` wheels include their own GDAL. On a `python:<version>-slim` image they need `libexpat1` in `apt-get`.

!!! note
    The GDAL Python bindings in the OSGeo images are built against NumPy 1.x. `from osgeo import gdal` works with NumPy 2, but `osgeo.gdal_array` and the calls that use it, such as `ReadAsArray` and `WriteArray`, need `numpy<2` in `requirements`.

!!! note
    With `conda: true`, a Python version in the conda file must match `python-version`. For example, `python=3.10.14` in the conda file works with `python-version: "3.10"`, but not with `"3.12"`: the conda environment cannot be solved and the build fails.

The block runs as a non-root user: UID `10001`, or `mambauser` if `conda` is `true`. The user owns `/app`, so the block can write there, in `/tmp` and in its home directory.

!!! tip
    Clay installs no CUDA. PyTorch wheels include CUDA; with `conda: true`, install CUDA from conda (for example `pytorch-cuda`). [`gpu: true`](#gpu) only makes `clay run` give the container the GPUs.

---

### gpu

| | |
|---|---|
| **Key** | `gpu` |
| **Type** | `bool` |
| **Default** | `false` |

Whether the block needs a GPU. When set to `true`, `clay run` starts the container with `--gpus all`, and `clay publish` sends the value to the registry. It installs nothing in the image. `--gpus all` needs the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) on the host.

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

Environment variables that the Clay runtime sets when it creates the block, before `setup()` runs. A variable that is already set in the container, for example with `clay run -e`, keeps its value. Values are converted to text. These variables are not written into the Dockerfile.

Clay reads its own settings, such as `CALLBACK_ENDPOINT`, `INPUT_JSON` and the storage paths (sections 1 to 11 of [Environment Variables](env-requirements.md)), and downloads the `--input-uri` file before it applies `env`. So `env` cannot change them, and does not apply to that download.

```yaml
env:
  MODEL_CACHE_DIR: "/tmp/cache"
  LOG_LEVEL: "INFO"
```

!!! warning
    Do not put secrets (API keys, passwords) in `env`: `clay publish` sends `env` to the registry. Pass them when the block runs instead, for example with `clay run -e`.

---

## What Clay checks and when

| When | Checked by | What |
|---|---|---|
| Every command that reads `clay.yaml`: `clay build`, `clay run`, `clay push` without an image, `clay publish`, `clay dockerfile` | Clay CLI | YAML syntax, that `apiVersion` is supported, and the whole file against its [schema](#schema-and-editor-support): no unknown keys, required keys present, the type of each value, the allowed values of `kind`, `type`, `format`, `python-version` and the other fields, the form of `name` and `version`, and the `validation` rules allowed for each `format` |
| When Clay generates the Dockerfile | Clay CLI | `gdal: true` is not used with `"3.11"` without conda, and the project has a block package with an `entry.py` |
| `clay publish`, before the build | Clay CLI, by asking the registry | `name` and `version` are not already published |
| `clay publish`, after the image is built and pushed | Clay registry | `version` is a semantic version, `kind` is `block`, `type` is `processing`, `source` or `visualization`, and `name`, `apiVersion` and `author` are not empty |
| Block start | Python runtime | `inputs` and `outputs` exist (a block with no inputs needs `inputs: []`), and each parameter has `name`, `type` and `default` |
| Before `preprocess()` | Python runtime | The [validation rules](#validation-rules) of `string`, `number` and `date` inputs |
| After `postprocess()` | Python runtime | Each returned output is declared in `outputs`, and the `properties` keys are valid for its format |

!!! note "Defaults are not written into the published spec"
    `clay publish` sends `parameters`, `inputs`, `outputs` and `env` to the
    registry as written in `clay.yaml`, converted to JSON. Omitted fields such as
    `date_format` are absent from the stored spec; the runtime applies the
    default. Anything that reads specs from the registry must apply the same
    defaults itself. `build` is different: Clay rebuilds it from its known
    build fields, so an omitted build field is stored as `""`, `false` or
    `null`.

---

## Validation Rules

Add a `validation` field to an input to check its value before processing. The runtime checks `string`, `number` and `date` inputs. Rules on other formats are accepted but not checked.

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
      regex_match: '[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}\Z'
```

`regex_match` uses Python's `re.match`, so the pattern only has to match the start of the value. End the pattern with `\Z` to match the whole value. Do not use `$`: in Python it also matches before a trailing newline.

The Go `datatypes` package (`proto/go`) checks `regex_match` differently: the pattern can match anywhere in the value, and a pattern with `\Z` fails to compile.

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

### Date Validation

```yaml
inputs:
  - name: capture_date
    format: date
    type: str
    validation:
      date_format: date_only   # date_only (default) or date_time
      min_date: "2024-01-01"
      max_date: "2024-12-31"
```

| Field | Description |
|---|---|
| `date_format` | `date_only` accepts exactly `YYYY-MM-DD`. `date_time` accepts RFC 3339 and **requires a UTC offset** (`Z` or `+05:30`), so values are always comparable. Defaults to `date_only`. |
| `min_date` | Earliest allowed value, inclusive. Must use the same encoding as `date_format`. |
| `max_date` | Latest allowed value, inclusive. Must use the same encoding as `date_format`. |

Each bound is optional and checked independently. An empty value is treated as
unset rather than invalid, so a missing required input is reported as a missing
input, not as an out-of-range date. A malformed bound in the spec is an error.

### Area Validation (Raster/Vector)

`raster` and `vector` inputs accept `min_area` and `max_area`, in square meters. The Python runtime does not check them. The Go `datatypes` package (`proto/go`) checks them against the value's `area` field.

```yaml
inputs:
  - name: image
    format: raster
    type: url
    validation:
      min_area: 10
      max_area: 1000
```

---

## Complete Example

Here's a complete specification for an NDVI block:

```yaml
# yaml-language-server: $schema=https://pixxelhq.github.io/clay/schema/v1.json
apiVersion: clay/v1
kind: block
type: processing
name: ndvi-calculator
version: 1.0.0
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
