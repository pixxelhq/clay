---
title: FAQs
order: 13
---

# FAQ

### Why should I create projects with Clay?

Clay gives every block the same baseline structure, tooling and runtime. This helps in the following ways:

1. **A common project structure.** `clay new` and `clay init` create the same layout for every block: `clay.yaml`, a `block.py` with the `setup`, `preprocess`, `inference` and `postprocess` methods, sample inputs and a test. If you know one Clay block, you can read another.

2. **A generated Dockerfile.** `clay build` generates the `Dockerfile` from the `build` section of `clay.yaml` on every build, unless you pass `-f` or the project has its own `./Dockerfile`. You set the Python version, pip or conda, GDAL and apt packages there, so you do not need to write or maintain a `Dockerfile`, and blocks are built from the same templates.

3. **Typed inputs and outputs.** Inputs and outputs are declared in `clay.yaml` and use the types from the `datatypes` package (`Raster`, `Vector`, `Tabular`, `Date`, `String`, `Number`). After `setup` and the input download, and before `preprocess` runs, string, number and date inputs are checked against the `validation` rules in the spec. `validation` rules on raster, vector and tabular inputs are not checked.

4. **A runtime that handles the plumbing.** The runner downloads input files, uploads output files, sends status and progress callbacks, and writes structured JSON logs. Your block code stays separate from these details. If `setup` or the input download fails, the runner sends no callback; the process exits with the exception.

5. **A registry.** `clay publish` registers each block version in the Clay registry, so blocks can be found and versioned in one place.

!!! warning

    Keep the structure that Clay generates. The Dockerfile that `clay build` generates expects
    `clay.yaml` at the project root and the block package folder with `entry.py` next to it.

### What is the relevance of `is_artifact` in the data types?

`is_artifact` means that the data item has a file, and `value` holds the location of that file. For example, a `Raster` with `is_artifact` set to `true` has a TIFF file, and `value` is its path or URL.

It defaults to `true` for `Raster`, `Vector` and `Tabular`, and to `false` for `Date`, `String` and `Number`.

The runner uses it to move files:

* For an input with `is_artifact: true`, the runner downloads the file in `value` before `preprocess` runs and sets `value` to the local path. A `Vector` input whose `value` does not start with `http://`, `https://`, `s3://` or `file://` is treated as GeoJSON text and written to a `.geojson` file, so a local file path does not work as a vector input.
* For an output with `is_artifact: true`, the runner uploads the file in `value` to `REMOTE_OUTPUT_PATH` after `postprocess` returns. If `value` is empty or is not an existing file, the output is skipped silently: nothing is uploaded and `value` is not changed.

### Why is there an `InferenceCtx` type and why does `infer` return one?

`BlockWrapper.infer()` runs `preprocess`, `inference` and `postprocess` in order. Each block returns a different number of outputs, and the runner only learns them at runtime. So `infer()` collects every datatype that `postprocess` returns into an `InferenceCtx` object and returns it. The runner then reads the outputs from that object, uploads their files and writes their spec files.

`InferenceCtx` only holds the outputs. It does not carry inputs or callback data. The runner sends status and progress callbacks itself, and reads run settings such as `EXECUTION_ID` and `CALLBACK_ENDPOINT` from environment variables.

### Difference between `processing` and `source` blocks

The `type` field in `clay.yaml` says what kind of block it is:

By convention:

* **`processing`**: the block reads input data and analyses or transforms it, for example NDVI from a raster.
* **`source`**: the block fetches or generates data without needing input data, for example downloading imagery for an area.

The type is metadata. The runner runs every block the same way, whatever its type. The Clay registry checks the field when a block is added and accepts `processing`, `source` and `visualization`.

### Rules about returning results from a block

* `postprocess` returns a dict whose values are datatypes, such as `datatypes.Raster(...)`. Any other value, such as a plain number, a dict or one of the input objects that `preprocess` received, fails the run with `AssertionError`.
* The `name` of each returned datatype must match an output in the spec file, or the run fails with `KeyError`. The dict keys are not checked. An output that is declared in the spec but not returned is not an error.
* For an output with a file, such as a `Raster`, write the file locally and set `value` to its local path. The runner uploads it; see [`is_artifact`](#what-is-the-relevance-of-is_artifact-in-the-data-types).
* For types with *properties* (`Raster`, `Vector`, `Date`, `Tabular`), the runner merges the *properties* from the output definition in the spec into the returned output. Where the block code sets a property that the spec also sets, the block code's value is used.

!!! warning

    Properties set in the block code can then differ from the spec file. Clay does not check this.


### How to use `Discretization` in `RasterProperties`?

The intention behind the _discretization_ attribute is two-fold,

1. Represent a continuous distribution as an interval-based distribution (_i.e. discretize a continuous distribution_ ).

2. Represent additional information about an underlying distribution that is already discrete (_i.e. what classes and colors does each index represent_).

The object essentially communicates _three_ things,

* _Intervals / index values_ for the underlying distribution.
* _Classes_ represented by each interval / index.
* _Color_ for each class.

!!! note

    Use `interval` or `index` as the discretization `type`. The field is a free string: Clay does not check its value.

!!! note

    When the discretization type is `interval`, set `range` on each class. When it is `index`, set `value` on each class.

**Example for `index`-based discretization**

```python
import datatypes

target = datatypes.Raster(
    name="raster",
    type="url",
    value="some.tiff",
    properties=datatypes.RasterProperties(
        discretization=datatypes.Discretization(
            type="index",
            classes=[
                datatypes.DiscretizationClass(name="low-stress", value="1", color="#0000ff"),
                datatypes.DiscretizationClass(name="high-stress", value="2", color="#ff0000"),
            ],
        )
    ),
)
```

**Example for `interval`-based discretization**

```python
import datatypes

target = datatypes.Raster(
    name="raster",
    type="url",
    value="some.tiff",
    properties=datatypes.RasterProperties(
        discretization=datatypes.Discretization(
            type="interval",
            classes=[
                datatypes.DiscretizationClass(name="low-stress", range=datatypes.Range(min=-2, max=-1), color="#0000ff"),
                datatypes.DiscretizationClass(name="high-stress", range=datatypes.Range(min=1, max=2), color="#ff0000"),
            ],
        )
    ),
)
```
