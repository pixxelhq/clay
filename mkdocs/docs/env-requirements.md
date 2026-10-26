---
title: Environment Variables
order: 6
---

# Environment Variables Reference

This document details the environment variables used to configure and run a block locally or through an orchestrator. Each variable controls a distinct aspect of execution, data management, or orchestration. Understanding and setting these variables correctly ensures smooth and reproducible runs—whether executing single-block insights or workflows of chained blocks.

***

## 1. `EXECUTION_ID`

- **Purpose**: Uniquely identifies each block run instance.
- **Scope**: Used for tracing, auditing, and debugging execution logs and results. This ID is particularly important when the block communicates its status via callbacks, allowing the orchestrator to track which specific execution is reporting progress.
- **Best Practice**: Set by the orchestrator; must be globally unique for each run.
- **Usage in Callbacks**: When blocks report their status (success/failure, progress) to the callback endpoint, the EXECUTION_ID helps the orchestrator correlate the callback to the specific block run.

***


## 2. Passing input: `--input` and `--input-uri`

Input no longer arrives through a configurable env var. Clay parses two CLI flags in
`clay.Run()`, and they take precedence over every environment variable below:

| flag | carries |
|------|---------|
| `--input '<json>'` | the input array inline |
| `--input-uri '<uri>'` | a URI Clay downloads the array from (`s3://…`, or any configured storage backend) |

```bash
# directly
python entry.py --input '[{"format":"string","name":"index","type":"str","value":"TVI"}]'

# through the CLI, which forwards the flag to the container entrypoint
clay run my-block:v1.0.0 --input '[{"name":"raster","type":"url","format":"raster","value":"s3://…"}]'
clay run my-block:v1.0.0 --input "$(cat sample-input.json)"
```

If neither flag is given, Clay falls back to `INPUT_JSON_URI` and then `INPUT_JSON`
(section 4).

!!! warning "`INPUT_JSON_ENV_KEY` was removed"
    Clay used to read this to decide *which* env var held the input, which let Argo point
    it at `ARGO_TEMPLATE`. Argo stopped injecting `ARGO_TEMPLATE` into the main container in
    v3.6, so the indirection was dropped. Clay now always reads `INPUT_JSON`. Setting
    `INPUT_JSON_ENV_KEY` has no effect.

***

## 3. `INPUT_JSON_JQ_FILTER`

- **Purpose**: A [jq](https://stedolan.github.io/jq/) filter applied to the input JSON before
  Clay parses it. Set by Dexter on the **DAG/workflow** path only; never on the inference path.
- **Current value**:
  ```bash
  [.[] | .spec + {name: .name}]
  ```

**Why it exists.** On the DAG path Dexter cannot emit a flat spec array. Each input value is an
Argo reference (`{{inputs.parameters.<name>}}`) that Argo resolves to the *producing* task's
output spec — and that spec's embedded `name` is the producer's **output** name, not the name
this block declares. Argo substitutes plain text, so Dexter can only wrap the reference:

```bash
# what Dexter emits
--input '[{"name":"raster","spec":{{inputs.parameters.raster}}}]'

# what Argo resolves it to, e.g. from an upstream block whose output is called "result"
[{"name":"raster","spec":{"format":"raster","type":"url","name":"result","value":"s3://…"}}]

# what the filter turns it into — note `+ {name: .name}` overrides "result" with "raster"
[{"format":"raster","type":"url","name":"raster","value":"s3://…"}]
```

Clay keys inputs by name and then calls `preprocess(**inputs)`, so without the rename the block
would be invoked with `result=` instead of `raster=` and fail on a missing argument.

!!! note "Transitional"
    Block images ship their own copy of Clay, so this filter is what lets images built before
    the `--input` flag keep working. Once every block is rebuilt, Dexter stops setting it, the
    flatten moves into Clay, and the `jq` dependency is dropped.

***

## 4. `INPUT_JSON` and `INPUT_JSON_URI`

- **Purpose**: The env-var fallback for block input data, used when neither `--input` nor
  `--input-uri` is passed.
- **Format**: JSON string (typically a list of dictionaries, specifying `name`, `type`, `format`, and `value`).
- **Resolution order**: `--input-uri` → `--input` → `INPUT_JSON_URI` → `INPUT_JSON`. The first one
  set wins; an empty value reads the same as unset.
- **`INPUT_JSON_URI`**: a URI Clay downloads the array from instead of reading it inline. Dexter
  offloads inference inputs larger than 100KB here so the pod spec stays small.
- **Usage**: For local runs, set `INPUT_JSON` manually or use the test_block.py script, which sets
  it automatically. Prefer `--input` for new work.
- **Example**:
  <details>
  <summary>Show example JSON input</summary>
```json
[
{
        "name": "raster",
        "type": "url",
        "format": "raster",
        "value": "",
        "is_artifact": "true",
        "stac_url": "./tests/example_stac.json",
        "properties": {
            "bands": [
                "B01",
                "B02",
                "B03",
                "B04",
                "B05",
                "B06",
                "B07",
                "B08",
                "B09",
                "B11",
                "B12",
                "B8A",
                "SCL"
            ],
            "collection": "sentinel-2-l2a"
        }
    },
    {
        "format": "string",
        "name": "string",
        "type": "str",
        "value": "hello world"
    },
    {
        "name": "vector",
        "type": "url",
        "format": "vector",
        "is_artifact": "true",
        "value": "./tests/vector.geojson"
    }]
```
</details>

***

## 5. `LOCAL_ARTIFACT_DOWNLOAD_PATH`

- **Purpose**: Directory path on the local file system where downloaded artifacts (input files, data resources) are stored.
- **Default Value**: `/tmp/inputs`
- **Role**: Used for processing files (such as raster or vector data) needed by the block. Clay downloads remote files referenced in the input to this location before processing.
- **Best Practice**: Ensure path is writable and has enough storage when handling large datasets.

**Example:**
```bash
# Using default path:
# Files will be downloaded to /tmp/inputs/

# Custom download location:
export LOCAL_ARTIFACT_DOWNLOAD_PATH="/workspace/block_inputs"
# Files will be downloaded to /workspace/block_inputs/
```

***

## 6. `REMOTE_OUTPUT_PATH`

- **Purpose**: Specifies where to upload output artifacts produced by a block run.
- **Default Value**: `/tmp/clay/outputs`
- **Usage**: Output files which include result data are transferred to this remote location for downstream processing or client access. This can be a local path or an S3 location.

**Example:**
```bash
# Using default local path:
# Outputs will be uploaded to /tmp/clay/outputs/

# S3 remote storage:
export REMOTE_OUTPUT_PATH="s3://my-bucket/block-outputs/run-123/"
# Outputs will be uploaded to the specified S3 location

# Custom local path:
export REMOTE_OUTPUT_PATH="/shared/storage/outputs"
```

***

## 7. `REMOTE_INPUT_PATH`

- **Purpose**: Specifies the remote path for uploading input files before block execution.
- **Default Value**: `/tmp/clay/inputs`
- **Role**: Remote path (local or S3) where input files are uploaded after being downloaded from their original sources. This provides a staging area for block inputs.

**Example:**
```bash
# Using default local path:
# Inputs will be uploaded to /tmp/clay/inputs/

# S3 remote storage:
export REMOTE_INPUT_PATH="s3://my-bucket/block-inputs/run-123/"
# Input files will be uploaded to the specified S3 location

# Custom local path:
export REMOTE_INPUT_PATH="/shared/storage/inputs"
```

***


## 8. `OUTPUT_JSON_PATH`

- **Purpose**: Directory path where output specification files (e.g., `spec.json`) are stored locally.
- **Default Value**: `/tmp/clay/outputs/`
- **Usage**: Acts as a working directory for block outputs. The output specification file contains detailed metadata about the block's results including data properties, processing parameters, and other relevant information for end users.

***

## 9. `OUTPUT_JSON_BASE_FILE_NAME`

- **Purpose**: Name of the primary output specification file.
- **Default Value**: `spec.json`
- **Role**: This file contains the output specifications for end users, including detailed properties of the results such as raster properties, dates, metadata, and other output-specific information. The file is saved in the directory specified by `OUTPUT_JSON_PATH`.
- **Best Practice**: Avoid name collisions—ensure unique naming in parallel runs.

***


## 10. `CALLBACK_ENDPOINT`

- **Purpose**: The URL endpoint for the block to communicate runtime status and progress updates to the orchestrator.
- **Usage**: Facilitates reporting of block status (success/failure, progress metrics).
- **Note**: When running locally, this variable can be omitted.

***

## 11. `CALLBACK_HEADERS`

- **Purpose**: Provides additional headers (e.g., `userid`, `organisationid`) for authenticated callbacks.
- **Format**: JSON string containing relevant authentication info.
- **Note**: Skip this variable when running blocks locally.

***

## CLI environment variables

These variables configure the Clay CLI itself and are read on the host (not
inside the block container). They mirror the corresponding command-line flags.

### `CLAY_DOCKER_REGISTRY`

- **Purpose**: Docker image registry that `clay publish` pushes block images to.
- **Equivalent flag**: `--docker-registry`.
- **Used by**: `clay publish`.

### `CLAY_REGISTRY_HOST`

- **Purpose**: URL of the Clay block registry that the CLI talks to.
- **Equivalent flag**: `--clay-registry`.
- **Used by**: `clay publish`, `clay block list`, `clay block describe`.

***
