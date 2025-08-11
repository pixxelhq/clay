# API Reference


!!! warning "Types in Clay is being deprecated"

    We are in the process of deprecating existing *Types* implementation in Clay and move to newer external implementation. For more information please visit the [datatypes-schema docs](https://datatypes-schema.example.com/). The conceptual foundation is still the same, but the technical implementation and usage has changed slightly. You can read more about this in at [docs](https://datatypes-schema.example.com/). For tracking the model migration please check out this [linear ticket](https://linear.app/REDACTED/issue/REDACTED-TICKET/[tracker]-model-integration-with-datatypes-schema).

## Types

### Raster
::: clay.types.Raster

### Vector
::: clay.types.Vector

### Tabular
::: clay.types.TabularProperties

### Date
::: clay.types.Date

### String
::: clay.types.String

### Number
::: clay.types.Number

## Type Properties

### RasterProperties
::: clay.types.RasterProperties

### VectorProperties
::: clay.types.VectorProperties

### TabularProperties
::: clay.types.TabularProperties

### DateProperties
::: clay.types.DateProperties

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
