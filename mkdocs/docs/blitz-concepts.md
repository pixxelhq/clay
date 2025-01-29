# Five Minute Blitz

This document provides a (blazingly) fast overview of the critical concepts required for working with this tool (and frankly, rest of our system).

Each section provides a (really) concise explanation on a strictly *do-i-really-need-to-know-this* basis. However, we also provide references that cover these concepts in much greater detail.

## Types

!!! warning "Types in Clay are being deprecated"

    We are in the process of deprecating existing *Types* implementation in Clay and move to newer external implementation. For more information please visit the [datatypes-schema docs](https://datatypes-schema.example.com/). The conceptual foundation is still the same, but the technical implementation and usage has changed slightly. You can read more about this in at [docs](https://datatypes-schema.example.com/). For tracking the model migration please check out this [linear ticket](https://linear.app/REDACTED/issue/REDACTED-TICKET/[tracker]-model-integration-with-datatypes-schema).

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

## Adding models to different Orchestrator environments

*Orchestrator* is our internal service to orchestrate the running of models on our infrastructure. In order to provide bug free experience to our clients on platform, it is necessary that the models are well tested before being released to the clients.

To ensure this, we have different orchestrator environments: `develepment(dev)`, `staging(stg)` & `production(prod)`.

A model needs to be added into orchestrator database to be rendered in platform. To do so there are two options provided by clay:

* [Using Github Actions](usage.md#uploading-your-model-onto-orchestrator) (*recommended*)

    Adding a model to orchestrator is just a click away. Currently, a model can be added to only *dev* & *stg* envs.

    Model author needs to specify the *version* of model they are adding. Input syntax of version needs to follow semvar. For eg. *v0.0.1* or *v0.0.1-alpha*

    *   For adding model to *dev*, select the *development* env and provide a docker-tag which is optional. If docker-tag is not provided, latest SHA will be used as docker-tag while building the docker image.

        > Any docker-tag provided with suffix **"dev-"** will be deleted after a month from our docker registry

    *   For adding model to *stg*, select the *staging* environment option. In staging, *version* provided by author is used to generate a git tag and is also used as docker-tag.


* Using clay CLI

    The Clay CLI offers a command for adding a model to the Orchestrator database. While it's generally discouraged to use the CLI for adding blocks, there are specific scenarios where it can be utilized, such as adding a model to *production*.

    Add block command:

        clay add block <specFilePath> <flags>

       *   specFilePath is path to model spec file

       *   flags:

           -e, --env string   Environment to add new block to: dev, stg, prod (default "dev")

## How to update models

## Callbacks

## CLI

In addition to clay *package*, clay **CLI** is a tool to help model author as well as other teams to work with models. It provides functionalities like:

*   create a scaffolding for your model,

*   generating a dockerfile for model,

*   *add*, *update*, *list* and *get* blocks and *upload* model readmes.

[Command Reference](cli-reference.md) [![alt text](image-3.png)](cli-reference.md)
