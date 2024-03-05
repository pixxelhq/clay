# Five Minute Blitz

This document provides a (blazingly) fast overview of the critical concepts required for working with this tool (and frankly, rest of our system).

Each section provides a (really) concice explanation on a strictly *do-i-really-need-to-know-this* basis. However, we also provide references that cover these concepts in much greater detail.

## Types

All data flowing in and out of a model has a `type`. These types are high-level concepts that the broader system understands. Having all models adhere to a *type system* allows all models to talk to each other and allow us to *create long chains of models*.

>Think of it this way - since all models in the system speak the same language of inputs and outputs, they can talk to each other and pass their results to one another for further processing.

Currently, we support the following types of inputs and outputs,

* Raster
* Vector
* Number
* String
* Date
* Tabular

To get a more detailed explanation and usage please visit [here](types.md).

## ModelWrapper

The `ModelWrapper`, well, quite literally wraps a model. It essentially exposes four methods, *preprocess*, *inference*, *postprocess* and the optional *setup*. A sample usage looks like this,

```python

from clay import ModelWrapper, types

class Demo(ModelWrapper):
    def setup(self, x: int):
        self._x = x

    async def preprocess(self, i: types.String):
        print("hello ", i.Value)
        return {"value": i.Value}

    async def inference(self, value: str):
        # Do something
        return {"value": value}

    async def postprocess(self, value):
        return {"value": types.String(name="value", value:"value")}
```

## Runners

The *model* defined with `ModelWrapper` on it's own cannot be run on the infrastructure. Why? Because the infrastructure has very specific *needs* and in some cases, really complicated *wants*. On top of this, the infrastructure evolves with time and product diktats, and as a result, it's needs and wants also evolve.

Now, it is nearly impossible for every model author to stay abreast of every development activity happening (every bug fix, new feature and API change) around them and ensuring *every single model* under  their care remains compatible.

Hence, *Runners*. Very simple, *Runners* are abstractions that based on some conditions, make the best possible choice on *how to run* a model. If the model is running on the cluster, a different runner is used versus when the model is running locally on your computer.

As a model author, you should not care about this. All the model author has to do is, run the following function from the entrypoint,

```python
import clay

class MyModel(clay.ModelWrapper):
    pass

clay.Run(model=MyModel, name="mymodel", cfg_path="some/spec.json")
```

## Inputs and Outputs

All models require a set of inputs and produce another set of outputs. An unique challenge for our platform, is that these data items need to be consumed by other services and models. Hence they need to be present at particular locations, in a specified structure and following a certain format.

If you had the misfortune of dealing with Clay prior to `version 0.3.10a5`, then you might remember writing download or upload code using AWS S3 SDKs or worse, Azure Blob SDKs. Never again.

Post `v0.3.10a5`, all the responsibility of dealing with inputs and outputs would be *Clay's*. Meaning,

* The author always gets local file paths as inputs.
* The author always writes files locally.

It is *Clay's* responsibility to make sure the inputs and outputs end at the right location.

## The Model Specification

Each model needs to have specifications. Ideally, each model should have a specification for each environment that it runs in.

!!! warning

    The MLOPs team is working to ensure that a single specification works for all environments. Hence, the information mentioned here can change.

The specification illucidates the attributes of each model. This specification (or more commonly known as `spec`) is consumed by all aspects of our system, including the Frontend.

For a more detailed intro check [Block Specification](spec.md).


## CLI

To Be Added.
