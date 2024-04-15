# Block Specification
The spec file, such as `model_specifications_dev.yaml`, `model_specifications_stg.yaml`, and `model_specifications_prod.yaml`, is used to declare model information for deployment and compatibility with workflow and inference on the Platform platform. It defines:

* Model's input and output specifications
* Docker image building instructions
* Infrastructure requirements
* Options for running the model on GPU or other hardware accelerators

This is how the generate spec file looks like. 

```yaml
kind: block
type: processing
name: ndvi
version: 0.0.1
title: <Title for model to be displayed on the platform>
status: draft
description: describe the model
author: <please-fill-in-here>@pixxel.co.in
tags:
  - imagery
  - processing

resources:
  cpu:
    min: 1200m
    max: 4000m
  mem:
    min: 1200Mi
    max: 4000Mi
  gpu:
    min: 0
    max: 0

parameters: # model initialization params
  - name: weight
    type: int
    default: 5

inputs:
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
  requirements: #requirements.txt  or conda.yml

runtime_opts:
  image: REDACTED.dkr.ecr.us-east-2.amazonaws.com/ndvi:sample-version
  K8sJobConfig: null
  gpu: false

options:
  dry_run: null
  preview: null
  generate_k8s_spec: true

catalog_content_url: "" # model description url

```


The keys are exaplined below 

## Kind

* Key: `kind`
* Type: `str`

Specifies what kind of entity this spec file represents. This is a common attribute for every *entity* within our system but for models, it would always be `block`.

## Type

* Key: `type`
* Type: `str`

Type of the block. Can be `processing` or `source`. For more information regarding the difference, please read [this](faq.md#difference-between-processing-and-source-blocks). In essence, if the model is doing some sort of prediction / analysis, then the value should be `processing`.

## Name

* Key: `name`
* Type: `str`

This slug identifies the model uniquely. The string can only have **small case** alphanumeric characters. This identifier is used internally within the infrastructure and monitoring dashboards and is not displayed to the user.

!!! warning

    Once the `name` is set for a given model, it cannot be changed again. All subsequent models need to have the same
    `name`.

## Title

* Key: `title`
* Type: `str`

The display name of the model on Platform. This is the value that is shown to the user on the frontend.

!!! warning

    The `title` parameter once set for a given model, stays the same for all subsequent versions and cannot be changed without intervention from the MLOps team.

## Version

* Key: `version`
* Type: `str`

Version of the block. We follow [semantic versioning](https://semver.org/). This is a **required** field. If invalid, the block spec would be rejected.

!!! Note "Recommendation"

    The MLOps team recommends that versioning of the models are done as if they are software releases.

## Author

* Key: `author`
* Type: `str`

The individual responsible for maintaining this model. This is strictly for internal housekeeping purposes.

## Description

* Key: `description`
* Type: `str`

A single sentence describing what this model is and what it does.

## Tags

* Key: `tags`
* Type: `List[str]`

## Resources

* Key: `resources`

Specifies the resource requirements of the model.

### Fields
#### `cpu`
* Key: `cpu`
* Type: [`cpu`](#cpu_1)

#### `mem`
* Key: `mem`
* Type: [`memory`](#memory)

## Parameters

* Key:  `parameters`
* Type: [`parameter`](#parameter)

List of data items that are to be passed into the model during setup time.

## Inputs

List of inputs of the model. Each item of the list can be any of the types mentioned in [Types](types.md#fundamental-types).

!!! note

    Leave out the `value` field since this list is a `spec` list. Meaning, this list specifies what kind of inputs the model accepts and not the actual input values.

??? note "Example"

    ```yaml
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
    ```

## Outputs

List of outputs of the model. Each item of the list can be any of the types mentioned in [Types](types.md#fundamental-types).

!!! note

    Leave out the `value` field since this list is a `spec` list. Meaning, this list specifies what kind of outputs the model produces and not the actual output values.

??? note "Example"

    ```yaml
    outputs:
    - name: another_string
        format: string
        type: str
    - name: vector
        format: vector
        type: url
        properties:
        geometry: polygon

    ```


## Runtime Opts

* Key: `runtime_opts`

### Fields

#### `image`

* Key: `image`
* Type: `str`

The Docker image for this model. For most use-cases, this field would be populated by CI and automated build systems and require no intervention from the user.

#### `K8sJobConfig`
Legacy. Should be left to `null`. Would be removed by v1.0.0 stable release.

#### `gpu`

* Key: `gpu`
* Type: `bool`

`True` if the model requires a GPU. Defaults to `False`.

!!! warning

    Be careful with this option, because, well, GPUs are expensive!


## Build

Build time configurations for the model.

### Fields

#### `python-version`

* Key: `python-version`
* Type: `str`

Version of the Python runtime to be used in the docker image. Default is set to `3.9.1`.

!!! warning

    MLOps officially only supports `3.9.x` Python versions, but we are more than happy to discuss the requirement to support any other version. Please note, that it is highly recommended that you use backward compatible language features. Deviation from this and MLOps would not be able to guarantee behavior of the model during runtime. For example, using the [bitwise OR](https://docs.python.org/3/library/stdtypes.html#union-type) operator as a type union is one such example since it was introduced in `3.10.x` and is not a backward compatible language feature.

#### `conda`

* Key: `conda`
* Type: `bool`

If `True`, the the docker image would have `conda` as it's environment manager. Defaults to `False`. If set to `False`, no particular environment manager would be used.

#### `gdal`

* Key: `gdal`
* Type: `bool`

If `True`, GDAL would be installed at the operating system level within the docker image. Defaults to `False`.

#### `apt-get`

* Key: `apt-get`
* Type: `List[str]`

Any additional list of packages that need to be installed at the OS level within the docker image.

#### `requirements`

* Key: `requirements`
* Type: `str`

Relative path to the `requirements.txt` or `conda.yaml` that lists all the packages required by the model.

## Options

Leave to the defaults.

## Catalog Content URL

* Key: `catalog_content_url`
* Type: `str`

Path to the processed catalog markdown file. Automatically populated by Clay and requires no intervention from the user.

## Field Types

### CPU

#### Fields
* `min`

The minimum amount of CPU required by the model. The infrastructure setup **would guarantee** that the model would **at least** receive the specified
amount of compute time. The units are in `millicores (m)`. For more information about the unit, visit [here](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu).

For example, `2000m`, *roughly* means that the model would receive *2 cores* worth of compute.

* `max`

The maximum amount of CPU resource that can be used by the model. Any attempt to exceed this limit would result in the model being terminated. The infrastructure would do a *best effort attempt* to allocate this upper limit to the model. The units are in `millicores (m)`.

For example, `4000m`, *roughly* means that the model can access a maximum compute equivalent to *4 cores*.

### Memory

#### Fields

* `min`

The minimum amount of memory required by the model. The infrastructure setup **would guarantee** that the model would **at least** receive the specified amount of memory resources. The units are in `Mibibytes (Mi)`. For more information about the unit, visit [here](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory).

For example, `2000Mi`, *roughly* means that the model would receive around *2 GB*'s worth of memory.

* `max`

The maximum amount of the memory required by the model. This is a hard limit. Any attempt to exceed this limit would result in the model being terminated by the infrastructure. The units are in `Mibibytes (Mi)`.

For example, `5000Mi`, *roughly* means that the model can access a maximum memory equivalent to *5 GB*s.

!!! warning

    Please be very thoughtful and informed when choosing this hard bound. We have observed a lot of models being terminated because the upper bound was too low.

### Parameter

Data item that is to be passed into the model's `setup` function during startup time. The values defined here are treated as named parameters and would passed into the `setup` method as such.

#### Fields

* `name`

Name of the parameter. The value would be passed into the `setup` parameter as a named parameter with the same `name`.

* `type`

Data type of the parameter. Please note, that these are fundamental `Python` types hence the supported values are `Union[str, int, float, str]`.

* `default`

The default value for this parameter. This is passed as the value of the named argument to the `setup` function.

###
