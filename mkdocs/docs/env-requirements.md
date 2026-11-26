---
title: Environment Variables
order: 6
---

# Environment Variables Reference

These variables configure how the Clay runtime inside the block container reads its input, stores files and reports status. Clay reads sections 1 to 11 when the block starts, before it applies the [`env`](spec.md#env) section of `clay.yaml`, so `env` cannot set them. The last section lists the variables that the Clay CLI reads on the host.

***

## 1. `EXECUTION_ID`

- **Purpose**: The ID of the run. Clay sends it as `id` in every callback, so the receiver can tell runs apart.
- **Default Value**: `default_execution_id`
- **Note**: Clay does not check that it is unique.

***


## 2. Passing input: `--input` and `--input-uri`

`clay.Run()` reads two command-line flags. They take precedence over the `input_json` and
`input_uri` arguments of `clay.Run()` and over `INPUT_JSON_URI` and `INPUT_JSON` (section 4):

| flag | carries |
|------|---------|
| `--input '<json>'` | the input array inline |
| `--input-uri '<uri>'` | an `s3://` URI Clay downloads the array from. Other schemes are not supported |

```bash
# directly
python entry.py --input '[{"format":"string","name":"index","type":"str","value":"TVI"}]'

# through the CLI, which forwards the flag to the container entrypoint
clay run my-block:v1.0.0 --input '[{"name":"raster","type":"url","format":"raster","value":"s3://…"}]'
clay run my-block:v1.0.0 --input "$(cat sample-input.json)"
```

If neither flag is given, Clay falls back to `INPUT_JSON_URI` and then `INPUT_JSON`
(section 4).

!!! note
    Clay does not read `INPUT_JSON_ENV_KEY`. It always reads `INPUT_JSON`.

***

## 3. `INPUT_JSON_JQ_FILTER`

- **Purpose**: A [jq](https://jqlang.github.io/jq/) filter applied to the input JSON before
  Clay parses it. It applies to input from any source (`--input`, `--input-uri`,
  `INPUT_JSON_URI` or `INPUT_JSON`). If the filter fails, the block fails with
  `Failed to process input JSON with jq filter`.
- **Default**: unset, so the input JSON is used as is.
- **Example value**:
  ```bash
  [.[] | .spec + {name: .name}]
  ```

Use it when the tool that starts the block produces input JSON in another shape. With the
filter above:

```bash
# input
[{"name":"raster","spec":{"format":"raster","type":"url","name":"result","value":"s3://…"}}]

# after the filter: the input is named "raster", as preprocess() expects
[{"format":"raster","type":"url","name":"raster","value":"s3://…"}]
```

***

## 4. `INPUT_JSON` and `INPUT_JSON_URI`

- **Purpose**: The env-var fallback for block input data, used when neither `--input` nor
  `--input-uri` is passed.
- **Format**: JSON string (typically a list of dictionaries, specifying `name`, `type`, `format`, and `value`).
- **Resolution order**: `--input-uri` → `--input` → `INPUT_JSON_URI` → `INPUT_JSON` → `[{}]`.
  When a block is started from Python with
  `clay.Run(block, name, cfg_path, input_json=..., input_uri=...)`, those arguments come after
  the CLI flags and before the environment variables. If either CLI flag is passed, even empty,
  Clay ignores both arguments.
  The first one that is set and not empty wins. An empty `--input-uri`, `--input` or
  `INPUT_JSON_URI` reads the same as unset. `INPUT_JSON` is different: if it is set to an empty
  string, Clay uses it and fails to parse it as JSON.
- **No input**: If nothing is set, the input is `[{}]`. That item has no `format`, so the block
  fails with `KeyError: 'format'` before it sends any callback. A block with no inputs must get an
  empty list, for example `--input '[]'`.
- **`INPUT_JSON_URI`**: an `s3://` URI Clay downloads the array from instead of reading it
  inline. Use it for large inputs.
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
        "is_artifact": true,
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
        "is_artifact": true,
        "value": "s3://my-bucket/aoi/vector.geojson"
    }]
```
</details>

***

## 5. `LOCAL_ARTIFACT_DOWNLOAD_PATH`

- **Purpose**: Local directory where Clay puts the input files before `preprocess()`.
- **Default Value**: `/tmp/inputs`
- **Layout**: For each input whose `is_artifact` is `true`, Clay copies the local file or downloads
  the `s3://` file to `<LOCAL_ARTIFACT_DOWNLOAD_PATH>/<input_name>/<file>` and sets the input's
  `value` to that path. Other inputs are not fetched. Every input, artifact or not, also gets
  `<LOCAL_ARTIFACT_DOWNLOAD_PATH>/<input_name>/spec.json` with the input as JSON. For an artifact
  `raster` input with a `stac_url`, Clay also writes `stac.json` there. See
  [Input/Output & Datatypes](IO.md) for the values that work for each format.

**Example:**
```bash
export LOCAL_ARTIFACT_DOWNLOAD_PATH="/workspace/block_inputs"
# An artifact input "raster" with value s3://my-bucket/scene.tif is downloaded to
# /workspace/block_inputs/raster/scene.tif
```

***

## 6. `REMOTE_OUTPUT_PATH`

- **Purpose**: Where Clay puts the output files after `postprocess()`. A local path or an `s3://` URI.
- **Default Value**: `/tmp/clay/outputs`
- **Behavior**: For each output whose `is_artifact` is `true` and whose `value` is an existing
  local file, Clay copies or uploads the file to `<REMOTE_OUTPUT_PATH>/<output_name>/<file>` and
  sets the output's `value` to that path. Other outputs are skipped without a message.

**Example:**
```bash
export REMOTE_OUTPUT_PATH="s3://my-bucket/block-outputs/run-123/"
# An artifact output "result" with value /tmp/result.tif is uploaded to
# s3://my-bucket/block-outputs/run-123/result/result.tif
```

***

## 7. `REMOTE_INPUT_PATH`

- **Purpose**: Where Clay keeps a copy of the inputs. A local path or an `s3://` URI.
- **Default Value**: `/tmp/clay/inputs`
- **Behavior**: After it fetches the inputs, Clay copies or uploads everything in
  `LOCAL_ARTIFACT_DOWNLOAD_PATH`, including each input's `spec.json`, to this path, keeping the
  same layout.
- **`add_asset()`**: `self.add_asset(file_path, io_name, is_input)` uploads a file to
  `<REMOTE_INPUT_PATH>/inputs/<io_name>/<file>`, or `.../outputs/<io_name>/<file>` when
  `is_input` is `False`. It works only when `REMOTE_INPUT_PATH` is an `s3://` URI; with a local
  path it fails with `No storage provider available for protocol: file`.

**Example:**
```bash
export REMOTE_INPUT_PATH="s3://my-bucket/block-inputs/run-123/"
# /tmp/inputs/raster/scene.tif is uploaded to
# s3://my-bucket/block-inputs/run-123/raster/scene.tif
```

***


## 8. `OUTPUT_JSON_PATH`

- **Purpose**: Directory path where output specification files (e.g., `spec.json`) are stored locally.
- **Default Value**: `/tmp/clay/outputs/`
- **Layout**: Clay writes one file per output, to `<OUTPUT_JSON_PATH>/<output_name>/<OUTPUT_JSON_BASE_FILE_NAME>`.
  If `REMOTE_OUTPUT_PATH` is an `s3://` path, Clay also uploads each file to
  `<REMOTE_OUTPUT_PATH>/<output_name>/spec.json`.
- **Content**: Each file is one output as JSON, the same as in the success callback. Clay writes
  the files after it sends the success callback.

***

## 9. `OUTPUT_JSON_BASE_FILE_NAME`

- **Purpose**: Name of the primary output specification file.
- **Default Value**: `spec.json`
- **Role**: The file name of each output's JSON file, written to `<OUTPUT_JSON_PATH>/<output_name>/<OUTPUT_JSON_BASE_FILE_NAME>`.
- **Note**: The copy uploaded to `REMOTE_OUTPUT_PATH` is always named `spec.json`, whatever this variable says.

***


## 10. `CALLBACK_ENDPOINT`

- **Purpose**: The URL that the block sends its status and progress updates to.
- **Default Value**: `http://localhost:3000/callback`
- **Usage**: Clay sends each status update as a `POST` with the body `{"data": …}`. It retries up to
  3 times when it cannot connect. A callback that gets an HTTP error status is not retried. Only
  `200`, `202` and `204` count as success. If a callback fails, Clay logs the error and the
  block keeps running.
- **Errors without a callback**: An error in `setup()`, in reading the input JSON or in fetching
  the input files stops the block before the start callback, and Clay sends no failure callback.
  The container exits with an error and the traceback is in its log.
- **Note**: When running locally, this variable can be omitted. Callbacks to the default URL then
  fail and are only logged.

***

## 11. `CALLBACK_HEADERS`

- **Purpose**: Extra HTTP headers sent with each callback, for example for authentication.
- **Format**: A JSON object, for example `{"Authorization": "Bearer <token>"}`.
- **Default Value**: `{}`
- **Note**: If the value is not valid JSON, the block fails at start. Skip this variable when running blocks locally.

***

## 12. `AWS_ENDPOINT_URL`

- **Purpose**: Points the block's `s3://` reads and writes at an S3-compatible store other than AWS, such as MinIO.
- **Example**: `clay run my-block:v1.0.0 -e AWS_ENDPOINT_URL=http://host.docker.internal:9000 -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... --input "$(cat tests/sample_block_inputs.json)"`
- **Note**: Read by boto3 inside the block container, together with the usual AWS credential
  variables. Set it with `-e`, not in the `env` section of `clay.yaml`: Clay downloads the
  `--input-uri` file before it applies `env`. `clay run` starts the container without a
  `--network` option, so use a host that the container can reach, such as
  `host.docker.internal` on Docker Desktop, not `localhost`. `clay block assets` does not use
  it and accepts AWS S3 URLs only.

***

## CLI environment variables

These variables configure the Clay CLI itself and are read on the host (not
inside the block container). They mirror the corresponding command-line flags.

### `CLAY_DOCKER_REGISTRY`

- **Purpose**: Docker image registry that `clay publish` and `clay push` push block images to.
- **Equivalent flag**: `--docker-registry`. The flag wins over the variable.
- **Used by**: `clay publish`, and `clay push` when no image is given.

### `CLAY_REGISTRY_HOST`

- **Purpose**: URL of the Clay block registry that the CLI talks to.
- **Equivalent flag**: `--clay-registry`. The flag wins over the variable.
- **Used by**: `clay publish`. `clay block list` and `clay block describe` do not read it; pass `--clay-registry` to them.

***
