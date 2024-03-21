# Usage

To understand how to get started with Clay, we will be writing a simple model as a demonstration. Clay, is a tool that
_wraps your model_ and by definition, it is _not concerned with the internal working of your model_. In this example
too, we don't really care what the model is doing internally.

This usage guide is split into the following sections,

1. Creating your project.
2. Defining your inputs and outputs.
3. Writing and wrapping your model.
4. Defining your model spec file.
5. Generating dockerfile for you.
6. Uploading your model onto Orchestrator.

??? Note

    It is assumed that you have Clay installed on your system by now. If not, please visit [here](installation.md).

## What does our Model do?

* Accepts a `Raster`, `Vector` and `String` as inputs.
* Performs a fake operation on the `Raster`.
* Performs a fake operation on the `Vector` data and writes a new GeoJSON file. This file is an output of the model.
* Mutates the `String` input and returns a new `String`.

## Creating your project

For the sake of this example we will start from a fresh slate. Since this a Demo for Clay, we are going to call this
model `DemoClay`.

Before we proceed, if you are wondering why you should create your project with clay, please refer to
this [question here](faq.md#why-should-we-create-projects-with-clay).

The following command would create the project in the current directory by default. If you want to create the project in
some other directory, please feel free to provide the *directory path* instead of `.`

```shell
clay create project . DemoClay
```

## Defining your inputs and outputs

Now that we have our project up and running, we need to define the inputs and outputs to our model in it's spec file.

For our example, we will accept *three inputs* to our model,

1. A Raster file.
2. A Vector file.
3. A String Parameter.

Within the [`inputs`](spec.md#inputs) section of the model spec file, we enter the following blocks,

```yaml
- name: some_raster
  format: raster
  type: url
  is_artifact: true
  properties:

- name: some_vector
  format: vector
  type: url
  is_artifact: true
  properties:

- name: some_string
  format: string
  type: str
```

For our *outputs*, we define the following block within the [`outputs`](spec.md#outputs) section of our model spec file,

```yaml
  - name: another_string
    format: string
    type: str
  - name: vector
    format: vector
    type: url
    properties:
      geometry: polygon
```

## Defining your model spec file

We also need to setup our specification file. The *specification* file, quite literally, *specifies* the behaviour of
our model. Since all other systems and consumers would rely on the model specification during an interaction with the
model, it is *really important that we put a lot of thought into the contents and accuracy of our specification file*.
For more information please read  [about the model spec file](blitz-concepts.md#the-model-specification).

For our model, we need a setup parameter called `seed` that the model requires for every inference instance. To set this
value, we put the following code block in the `parameters` section of the file,

```yaml
parameters: # model initialization params
  - name: seed
    type: int
    default: 23

```

We also specify the resources that our model requires in the `resources` section,

```yaml

resources:
  cpu:
    min: 50m
    max: 100m
  mem:
    min: 100Mi
    max: 120Mi
```

Then entire file for *the dev environment* is as follows,

```yaml
kind: block
type: processing
name: DemoClay
version: 0.0.1
title: Model to Demo Clay
status: released
description: A Demo Model
author: marketplace@pixxel.co.in
tags:
  - imagery
  - processing

resources:
  cpu:
    min: 50m
    max: 100m
  mem:
    min: 100Mi
    max: 120Mi

parameters: # model initialization params
  - name: seed
    type: int
    default: 23

inputs:
  - name: some_raster
    format: raster
    type: url
    is_artifact: true
    properties:
  - name: some_vector
    format: vector
    type: url
    is_artifact: true
    properties:
  - name: some_string
    format: string
    type: str

outputs:
  - name: another_string
    format: string
    type: str
  - name: vector
    format: vector
    type: url
    properties:
      geometry: polygon

build:
  python-version: "3.10"
  conda: false
  gdal: true
  apt-get:
    - wget
  requirements: requirements.txt # or conda.yaml

runtime_opts:
  image: REDACTED.dkr.ecr.us-east-2.amazonaws.com/democlay:sample-version
  K8sJobConfig: null
  gpu: false

options:
  dry_run: null
  preview: null
  generate_k8s_spec: true

catalog_content_url: "" # modeldescription url
```

## Generate dockerfile

Only after populating the model spec file, model author should generate the dockerfile for the model.
This is cruical as the dockerfile can be have `pip` or `conda` as its environment manager based upoun the `requirements`
provided.

In order to generate a dockerfile, author can run the following `make` cmd:

```make
  make dockerfile
```

> In cases where model uses GPU, by default `conda` will be the environment manager.

## Writing and wrapping your model

At this point, we have our project and linters setup, inputs and outputs are defined. Next up, we have to undertake the
most important step of the process - *writing the actual model!*

Before we proceed, let rehash a couple of things,

1. Ideally, the model author has no need to touch the `entry.py` file created by Clay.
2. `model.py` defines the entrypoint model that has already subclassed `ModelWrapper`.
3. The `setup` method would receive the values defined in the `parameters` section of the model spec file.

Now, onto the model-writing process.

We also define a file called `geo.py`.
This [defines a fake mosaicing function](https://github.com/example/DemoClay/blob/a968314bf720ed0464a8db6f203087929ae96101/DemoClay/geo.py#L6)
that will be called from our model.

You can find the `model.py` for reference [here](https://github.com/example/DemoClay/blob/main/DemoClay/model.py).

Couple of things stand require your special attention,

* We import the clay types as `from clay import Types as T`.

* In
  the [`geo.mosaic`](https://github.com/example/DemoClay/blob/a968314bf720ed0464a8db6f203087929ae96101/DemoClay/geo.py#L7)
  module, while we pass in the whole `Raster` data item, we access the actual path to the tiff file via reading
  the `.Value` attribute. We also read the file via the standard `rasterio.open` method.

```python
example_raster = rio.open(r.Value)
```

* We also read the vector file by accessing the `.Value` attribute of the `Vector` data type (
  i.e. [variable `v` in the scope](https://github.com/example/DemoClay/blob/a968314bf720ed0464a8db6f203087929ae96101/DemoClay/model.py#L32)).

```python
with open(str(v.Value), "r") as f:
    v = geojson.load(f)
```

* Similarly,
  we [access the string](https://github.com/example/DemoClay/blob/a968314bf720ed0464a8db6f203087929ae96101/DemoClay/model.py#L40)
  value, mutate it and create a new string object.

```python
# mutating the string
val = str(s.Value)
new_string = "new string: " + val
```

* *Now we arrive at a critical juncture.*

We have to return the results of the model. Returning outputs are governed
by [some rules](faq.md#rules-about-returning-results-from-a-model). We return our output like,

```python
 return {
    "another_string": T.String(name="another_string", value=new_string),
    "vector": T.Vector(name="vector", value="my-vector.geojson"),
}
```

### Tip: logging helpful information

Clay provides logging functionality in `ModelWrapper` through it's `self.logger` attribute. You can and should use it to
print out useful information at various stages of the model pipeline.

We prefer using the `logger` instead of `print` statements because it provides a lot of extra information for free which
can be helpful during debugging.

Using the logger is very simple:

```python
# instead of this:
print("preprocessing complete")
```

```text
preprocessing complete
```

```python
# we do this:
self.logger.info("preprocessing complete")
```

```json
{
  "level": "INFO",
  "timestamp": "2024-03-21T05:28:27.435454Z",
  "logger": "DemoClay",
  "loc": "model.py:preprocess:67",
  "message": "preprocessing complete"
}
/* This has been formatted in multiple lines for the purposes of this doc.*/
/* The actual output is on a single line*/
```

As you can see, right off the bat we get some extra information with zero effort from our side:

- Level: the severity of the message.
    - This can be one of: `DEBUG`, `INFO`, `WARNING`, or `ERROR`, with severity increasing in that order
- Timestamp: the exact time at which this message was logged
- Logger: the name of the logger object used for this message. You will see other loggers from Clay printing other
  useful pieces of information as well.
- Loc[ation]: the exact file, function and line number of the location where the log was triggered
- Message: your actual log message

You can manually create loggers using clay very simply like so:

```python
import logging
from clay.logger import ClayLogger

logger = ClayLogger(logger_name='my-logger', level=logging.INFO)

logger.debug("This message will not be shown if level is set to INFO")
logger.info("This message and all messages at WARNING and ERROR level will be shown")
logger.warning("Warnings in scenarios such as when results can be computed but not necessarily with high quality")
logger.error("Reserved for situations where execution can generally not move forward", exc_info=exception_object)
```

You can learn more about [logging in python here](https://realpython.com/python-logging/)

## Don't forget the readme

As the tedious job of writing the model is done, take a minute to provide the description of the model in the
*catalog_readme* folder.

`model-README.md` file has two sections:

* Metadata

  ```metadata
  ---
  name: Name of model
  author: authorname
  input-img: ![]({{ addUrl "sample_input.png" }})
  output-img: ![]({{ addUrl "sample_output.png" }})
  inputs: {input1: "input description", input2: "input description"}
  outputs: {output1: "output description", output2: "output description" }
  ---
  ```

Go ahead and fill the details about your model in this section except for the `input-img` and `output-img`.

* Rest of the section is upto the model author to provide the information as they would like to be displayed on the
  platform

* Make sure to provide a `sample_input.png` and `sample_output.png` for the model in the *catalog_readme* folder.

And you are done...!

## Setup your github repo

Before adding the model to orchestrator using Github actions, there are a few *secrets* that needs to be added to the github
repo at:
`https://github.com/example/<model_name>/settings/secrets/actions`

* CLAY_BIN_DOWNLOAD_TOKEN
  > Generate a Personal Access Token (PAT) (classic) on Github, and set it as CLAY_BIN_DOWNLOAD_TOKEN. You can follow
  Github's
  documentation [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic).
  >
  > The minimum permissions are `repo` and `workflow`.

* AUTH_ORG_IDS
* AUTH_SUB
  > Connect with MLOps team for the above two tokens.

## Uploading your model onto Orchestrator

The process of adding a block to Orchestrator has the following steps,

1. Build the Docker Image and push to [AWS ECR](https://aws.amazon.com/ecr/).
2. Add the model to any one of the Orchestrator environments. **Note that the process of adding a block to each environment is
   slightly different**. (We cover this in more
   detail [here](blitz-concepts.md#adding-models-to-different-orchestrator-environments))

For the sake of simplicity in this example, we *only be adding the block to the dev environment*.

The steps to accomplish the above is as follows,

1. Head over to the `https://github.com/example/<model_name>/actions/workflows/package-deploy-model-aws.yaml` tab. For
   us, it is *https://github.com/example/DemoClay/actions/workflows/package-deploy-model-aws.yaml*.

2. Select the branch you want to deploy. Then enter the version you want to set the model as and an optional docker
   image tag.

3. Select the environment to add the model to.

   ![alt text](image-2.png)

4. Hit `Run Workflow`!.

If the workflow runs successfully, then your model should be pushed into Orchestrator and ready to be used!
