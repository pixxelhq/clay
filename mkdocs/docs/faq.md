---
title: FAQs
order: 13
---

# FAQ

### Why should I create projects with Clay?

Clay gives every block the same baseline structure, tooling and runtime. This helps in the following ways:

1. **A common project structure.** `clay new` and `clay init` create the same layout for every block: `clay.yaml`, a `block.py` with the `setup`, `preprocess`, `inference` and `postprocess` methods, sample inputs and a test. If you know one Clay block, you can read another.

2. **A generated Dockerfile.** `clay build` generates the `Dockerfile` from the `build` section of `clay.yaml` on every build. You set the Python version, pip or conda, GDAL and apt packages there. You do not write or maintain your own `Dockerfile`, and every block is built from the same tested templates.

3. **Typed inputs and outputs.** Inputs and outputs are declared in `clay.yaml` and use the types from the `datatypes` package (`Raster`, `Vector`, `Tabular`, `Date`, `String`, `Number`). Before your code runs, string, number and date inputs are checked against the `validation` rules in the spec.

4. **A runtime that handles the plumbing.** The runner downloads input files, uploads output files, sends status and progress callbacks, and writes structured JSON logs. Your block code stays separate from these details.

5. **A registry.** `clay publish` registers each block version in the Clay registry, so blocks can be found and versioned in one place.

!!! warning

    Deviation from `Clay` recommended tooling and structure is highly _not recommended_,
    unless absolutely necessary.

### What is the relevance of `is_artifact` in the data types?

`is_artifact` basically means that that this data item has an asset associated with it. Generally, the location
of the asset would be stored in the `value` attribute of the same data item.

For example, if the `is_artifact` attribute for the `Raster` datatype is set to `True`, this would mean that this
data item has a supporting asset (in this case a TIFF file) and the location of the tiff file would be in the `value`
parameter.

### Why is there an `InferenceCtx` type and why does `infer` return one?

`BlockWrapper.infer()` runs `preprocess`, `inference` and `postprocess` in order. Each block returns a different number of outputs, and the runner only learns them at runtime. So `infer()` collects every datatype that `postprocess` returns into an `InferenceCtx` object and returns it. The runner then reads the outputs from that object, uploads their files and writes their spec files.

`InferenceCtx` only holds the outputs. It does not carry inputs or callback data. The runner sends status and progress callbacks itself, and reads run settings such as `EXECUTION_ID` and `CALLBACK_ENDPOINT` from environment variables.

### Difference between `processing` and `source` blocks

The `type` field in `clay.yaml` says what kind of block it is:

* **`processing`**: the block reads input data and analyses or transforms it, for example NDVI from a raster.
* **`source`**: the block fetches or generates data without needing input data, for example downloading imagery for an area.

The type is metadata. The runner runs every block the same way, whatever its type. The Clay registry checks the field when a block is added and accepts `processing`, `source` and `visualization`.

### Rules about returning results from a block

* Names of the block outputs should be exactly same as the output items defined in the spec file. Any deviation would result in a runtime exception.
* Only standard type constructors (example: `Raster(...)` etc) should be used while returning outputs. Type constructors only allow the user to mutate *mutable fields of the type*.
* Some types almost always would have a supporting asset. For example, if a block output is of the `Raster` type, then there *is going* to be a TIFF file that is present locally and needs to saved remotely as a block output. In situations like this the `value` attribute would simply be the *local path of the file*.
* If a type support *properties* (`Raster`, `Vector`, `Date`, `Tabular`), by default, the *properties* defined in the output definition would be used in constructing the output. *If the user however* provides some custom properties within the block code, **these values would be used**.

!!! warning

    This is an unsafe operation as it could lead to de-sync between the spec file and the actual block output. Going forward we will be putting more precise safeguards.


### How to use `Discretization` in `RasterProperties`?

The intention behind the _discretization_ attribute is two-fold,

1. Represent a continuous distribution as an interval-based distribution (_i.e. discretize a continuous distribution_ ).

2. Represent additional information about an underlying distribution that is already discrete (_i.e. what classes and colors does each index represent_).

The object essentially communicates _three_ things,

* _Intervals / index values_ for the underlying distribution.
* _Classes_ represented by each interval / index.
* _Color_ for each class.

!!! note

    We only support two types of discretization: `interval` and `index`.

!!! note

    When our discretization type is `interval` we specify the `range` attribute. When our discretization type is `index`, we specify the `value` attribute.

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
