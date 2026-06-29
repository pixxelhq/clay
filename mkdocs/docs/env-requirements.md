# Environment Variables Reference

This document details the environment variables used to configure and run a block locally or through an orchestrator. Each variable controls a distinct aspect of execution, data management, or orchestration. Understanding and setting these variables correctly ensures smooth and reproducible runs—whether executing single-block insights or workflows of chained blocks.

***

## 1. `EXECUTION_ID`

- **Purpose**: Uniquely identifies each block run instance.
- **Scope**: Used for tracing, auditing, and debugging execution logs and results. This ID is particularly important when the block communicates its status via callbacks, allowing the orchestrator to track which specific execution is reporting progress.
- **Best Practice**: Set by the orchestrator; must be globally unique for each run.
- **Usage in Callbacks**: When blocks report their status (success/failure, progress) to the callback endpoint, the EXECUTION_ID helps the orchestrator correlate the callback to the specific block run.

***


## 2. `INPUT_JSON_ENV_KEY`

**Purpose:**
Provides flexibility for different execution environments by specifying which environment variable contains the block's input data. This design allows Clay to work seamlessly with various orchestrators and execution contexts.

**How it works:**
- Clay reads the value of `INPUT_JSON_ENV_KEY` to determine which environment variable contains the actual input data
- If `INPUT_JSON_ENV_KEY` is not set, Clay defaults to reading from the `INPUT_JSON` environment variable
- This two-level approach enables different executors (Kubernetes, Argo Workflows, etc.) to inject input data through their preferred environment variables

**Example:**
```bash
# Kubernetes executor might set:
export INPUT_JSON_ENV_KEY="K8S_BLOCK_INPUT"
export K8S_BLOCK_INPUT='[{"name": "data", "type": "url", "value": "s3://bucket/file.tif"}]'

# Argo Workflows executor might set:
export INPUT_JSON_ENV_KEY="ARGO_TEMPLATE"
export ARGO_TEMPLATE='{"inputs": {"parameters": [...]}}'

# Local execution (default):
# If INPUT_JSON_ENV_KEY is not set, Clay reads from INPUT_JSON directly
export INPUT_JSON='[{"name": "data", "type": "url", "value": "s3://bucket/file.tif"}]'
```

***

## 3. `INPUT_JSON_JQ_FILTER`

- **Purpose**: Defines a [jq](https://stedolan.github.io/jq/) filter for parsing input JSON, especially within workflows.
- **Default Value**:
  ```bash
  [.inputs.parameters[] | (.value | fromjson) + {name: .name}]
  ```
- **Usage**: Processes parameterized inputs in workflow scenarios by transforming, filtering, or extracting specific values needed for block consumption.

**Example:**
```bash
# Argo Workflows template input:
export ARGO_TEMPLATE='{
  "inputs": {
    "parameters": [
      {"name": "image", "value": "{\"type\": \"url\", \"format\": \"raster\", \"value\": \"s3://bucket/image.tif\"}"},
      {"name": "threshold", "value": "{\"type\": \"float\", \"value\": 0.5}"}
    ]
  }
}'

# With the default jq filter, this gets transformed to:
# [
#   {"name": "image", "type": "url", "format": "raster", "value": "s3://bucket/image.tif"},
#   {"name": "threshold", "type": "float", "value": 0.5}
# ]

# Custom jq filter for different input structure:
export INPUT_JSON_JQ_FILTER='[.data[] | {name: .id, type: .dataType, value: .path}]'
```

***

## 4. `INPUT_JSON`

- **Purpose**: The default environment variable for block input data. This is used when `INPUT_JSON_ENV_KEY` is not set.
- **Format**: JSON string (typically a list of dictionaries, specifying `name`, `type`, `format`, and `value`).
- **Usage**: This is the fallback input source. When `INPUT_JSON_ENV_KEY` is not specified, Clay reads input data directly from this variable. For local runs, users can set it manually or use the test_block.py script which sets it automatically.
- **Relationship to INPUT_JSON_ENV_KEY**: If `INPUT_JSON_ENV_KEY` is set to a value like "CUSTOM_INPUT", Clay will read from the `CUSTOM_INPUT` environment variable instead of `INPUT_JSON`.
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
