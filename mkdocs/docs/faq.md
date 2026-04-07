# FAQ

### Why should we create projects with Clay?

You should create projects with _Clay_ since it enforces a uniformity in baseline project structure,
tooling, coding practices, automation and quality control.

Enforcing a baseline uniformity helps us in the following ways,

1. Having a _minimum_ common structure allows the marketplace team to apply a _bunch of automations_
that help all teams speed up their _build, test and deployment_ lifecycles. For example, automated
_tag_ creation during promoting a block to _staging_ environment from _development_ allows us to track
block deployment histories more effectively. A common structure allows makes life really easier for the
marketplace team to debug issues as they happen post deployment.

2. It's no secret that Python's packaging tools are _not the best_. Changing from a well-known environment
manager to a new hot thing, would often mean the introduction of silent dependency bugs that would show up
weeks or even months later. All these problems and we haven't yet gotten to the complicated dance between CUDA, GDAL and
Kubernetes. Over the last couple of months, the marketplace team has deployed and managed, both GPU and non-GPU based
blocks and dealt with their fair share of runtime bugs and complexity. Having undergone the baptism, _we have settled
on two baseline environment configurations_ that we feel fairly confident in their efficacy and flexibility and
our ability to maintain and debug such environments on and off production.

3. Standard coding practices across blocks codebases allow for the proliferation of common standards of code hygiene
and style. Not only this allows for the better _and more beautiful_ code output, on a more practical note, it makes
a new hire's onboarding process much easier, since they don't have to adapt to every new codebase over and over again.

4. Clay provides tooling that help blocks run on our infrastructure. A prime example of this are _callbacks_. Status
and metric reporting via callbacks, IO processing and management, logging etc are all abstracted away from the block
code to ensure that it is insulated from the details of the infrastructure as much as possible.

!!! warning

    Deviation from `Clay` recommended tooling and structure is highly _not recommended_,
    unless absolutely necessary.

### What is the relevance of `is_artifact` in the data types?

`is_artifact` basically means that that this data item has an asset associated with it. Generally, the location
of the asset would be stored in the `value` attribute of the same data item.

For example, if the `is_artifact` attribute for the `Raster` datatype is set to `True`, this would mean that this
data item has a supporting asset (in this case a TIFF file) and the location of the tiff file would be in the `Value`
parameter.

### Why do we have a `InferenceCtx` type and why does `infer` return a `InferenceCtx`?

There are two reasons for taking this approach,

1. Certain data points, unrelated to the block inputs but related to the particular inference run are required for reporting data back
to Orchestrator like status, errors, time of execution among other things. Injecting these scoped data items into the pod environment _would mean
that we won't be able to support persistent pods_ should the need arise in the future. Hence adopting this methodology, gives us the flexibility and freedom to support trainsient pods now and persistent pods in the future if required.

2. Another reason, is that the block is an attribute of the runner. Hence, we need a common set of arguments to pass into the block and a
a common set of return values. The problem is that each block can have a variable number of inputs and outputs and the runner becomes aware
of the IO specification of the block only at runtime. Hence we we pass an `InferenceCtx` object in and out of the block. Inputs and outputs
are lists defined on the object, thus solving their variable length problem. On top this, `InferenceCtx` has inference specific data items
that the `BlockWrapper` can use to fire callbacks to Orchestrator updating state, time metrics etc.

### Difference between `processing` and `source` blocks

### Rules about returning results from a block

* Names of the block outputs should be exactly same as the output items defined in the spec file. Any deviation would result in a runtime exception.
* Only standard type constructors (example: `Raster(...)` etc) should be used while returning outputs. Type constructors only allow the user to mutate *mutable fields of the type*.
* Some types almost always would have a supporting asset. For example, if a block output is of the `Raster` type, then there *is going* to be a TIFF file that is present locally and needs to saved remotely as a block output. In situations like this the `Value` attribute would simply be the *local path of the file*.
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
target = types.Raster(
        name="raster",
        type="url",
        value="some.tiff",
        properties=types.RasterProperties(
            Discretization=types.RasterDiscretization(
                Type="index",
                Classes=[
                    types.DiscretizationItem(Name="low-stress", Value="1", Color="blue"),
                    types.DiscretizationItem(Name="high-stress", Value="2", Color="red"),
                ],
            )
        ),
    )
```

**Example for `interval`-based discretization**

```python
target = types.Raster(
        name="raster",
        type="url",
        value="some.tiff",
        properties=types.RasterProperties(
            Discretization=types.RasterDiscretization(
                Type="interval",
                Classes=[
                    types.DiscretizationItem(Name="low-stress", Range=[-2, -1], Color="blue"),
                    types.DiscretizationItem(Name="high-stress", Range=[1, 2], Color="red"),
                ],
            )
        ),
    )
```
