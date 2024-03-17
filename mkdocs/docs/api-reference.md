# API Reference

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

### Execution Modes
::: clay.run.SupportedExecutors

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
::: clay.runners.job_runner.JobRunner

### JobRunnerV2
::: clay.runners.job_runner_v2.JobRunnerV2

## Exceptions

### FailedExecutionException
::: clay.exceptions.FailedExecutionException

## Signals

### success
::: clay._signals.success

### failure
::: clay._signals.failure
