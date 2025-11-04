# API Reference


!!! warning "Types in Clay is deprecated"

## Datatypes

The datatypes package provides strongly-typed interfaces for working with various data formats. See the [Datatypes Guide](datatypes.md) for detailed usage instructions.

### DataWrapper

::: datatypes.data.DataWrapper
    options:
      show_root_heading: true
      heading_level: 4
      members_order: source
      show_source: true

### DataWrapper Interface

::: datatypes.data.DataWrapperInterface
    options:
      show_root_heading: true
      heading_level: 4
      members_order: source
      show_source: true

### Helper Functions

#### RasterFromDict
::: datatypes.data.RasterFromDict
    options:
      show_root_heading: true
      heading_level: 5

#### VectorFromDict
::: datatypes.data.VectorFromDict
    options:
      show_root_heading: true
      heading_level: 5

#### TabularFromDict
::: datatypes.data.TabularFromDict
    options:
      show_root_heading: true
      heading_level: 5

#### DateFromDict
::: datatypes.data.DateFromDict
    options:
      show_root_heading: true
      heading_level: 5

#### StringFromDict
::: datatypes.data.StringFromDict
    options:
      show_root_heading: true
      heading_level: 5

#### NumberFromDict
::: datatypes.data.NumberFromDict
    options:
      show_root_heading: true
      heading_level: 5

#### FromDict
::: datatypes.data.FromDict
    options:
      show_root_heading: true
      heading_level: 5

### Exceptions

#### DataWrapperError
::: datatypes.data.DataWrapperError
    options:
      show_root_heading: true
      heading_level: 5

#### FieldNotFoundError
::: datatypes.data.FieldNotFoundError
    options:
      show_root_heading: true
      heading_level: 5

#### InvalidFieldTypeError
::: datatypes.data.InvalidFieldTypeError
    options:
      show_root_heading: true
      heading_level: 5

#### UnsupportedFieldTypeError
::: datatypes.data.UnsupportedFieldTypeError
    options:
      show_root_heading: true
      heading_level: 5

## Core

### Run
::: clay.Run

### ModelWrapper
::: clay.core.ModelWrapper
    selection:
        filters:
            - "!receive_raw_inputs"
            - "!__init_subclass__"
            - "!_dep_parse_inputs"
        members_order: source

### InferenceOpts
::: clay.types.InferenceOpts

### InferenceCtx
::: clay.core.InferenceCtx

## Runners

### JobRunner
::: clay.runners.runner.JobRunner

## Exceptions

### FailedExecutionException
::: clay.exceptions.FailedExecutionException
