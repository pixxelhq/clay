---
title: Block Development Tutorial
order: 9
---

# Block Development
This tutorial builds a block that computes NDVI from a Sentinel-2 raster.

## Prerequisite

* Install the Clay CLI as described in [Getting Started](getting-started.md).
* Create the project with `clay new ndvi`, then `cd ndvi`. The block name `ndvi` gives the package folder `ndvi/`, the class `Ndvi` and the image `ndvi:v0.0.1`. `ndvi/entry.py` and `tests/test_block.py` import the class `Ndvi` from `ndvi/block.py`, so keep that class name.
* Familiarity with [Types](IO.md) and the [Block Specification Format](spec.md).



## Development

A block class has four methods:

1. `setup`: Called once, from the block's constructor, before the inputs are downloaded. It gets the `default` of each entry in `parameters` in `clay.yaml`. Load weights and other resources here. The base class raises `NotImplementedError`, so the block must define it.
2. `preprocess`: Gets the inputs. Check or prepare them here.
3. `inference`: Runs the block's algorithm.
4. `postprocess`: Returns the outputs as datatypes.

`clay new` generates `ndvi/block.py` with these methods. Replace them with the code below.

### 1. Define the setup() method.

The block reads the list of bands used for NDVI from the `bands` parameter.

```python
def setup(self, bands: List[str]) -> None:  # type: ignore
    self.bands = bands
```

### 2. Define `preprocess()` method.

1. `raster` is the input named `raster`. Clay passes a view of the `Raster` datatype: its fields, such as `properties`, work as on the datatype, and `value` is converted to the input's `type` (for `url` it stays a string). By the time `preprocess` runs, `value` is the local path of the downloaded file.
2. It checks that the raster is from the Sentinel-2 collection `sentinel-s2-l2a-cogs`.
3. If the check fails, it calls `clay.failure()`. This raises a `FailedExecutionException`, which stops the run and reports the message as the failure reason.

```python
async def preprocess(  # type: ignore
    self,
    raster: datatypes.Raster
) -> Dict[str, Any]:
    self.logger.warning(
        "In pre-process. Use self.logger for all logging. Avoid print statements"
    )

    if raster.properties.collection != "sentinel-s2-l2a-cogs":
        clay.failure(f"unsupported collection: {raster.properties.collection!r}")
    self.logger.info("preprocess has been completed, moving on to inference")
    return {"raster": raster}
```

### 3. Define `inference()` method.

`inference` gets the keys of the dict that `preprocess` returns as arguments. It reads the bands named in `self.bands`, computes NDVI and returns the NDVI array and the raster's metadata. rasterio band indexes start at 1, so the code reads band `idx + 1`. The bands are converted to `float32` before the division.

```python
async def inference(self, raster: datatypes.Raster) -> Dict[str, Any]:  # type: ignore
    raster_value = rasterio.open(raster.value)
    required_bands = {}
    for bi in self.bands:
        self.logger.info(f"looking for band {bi} in raster band-list")
        idx = list(raster.properties.bands).index(bi)
        required_bands[bi] = raster_value.read(idx + 1).astype("float32")

    ndvi = (required_bands["B08"] - required_bands["B04"]) / (required_bands["B08"] + required_bands["B04"])
    self.logger.info(f"shape of calculated ndvi raster: {ndvi.shape}")
    self.logger.info("inference has been completed, moving on to postprocess")
    return {"ndvi": ndvi, "meta": raster_value.meta}
```

### 4. Define `postprocess` method.
`postprocess` gets the keys of the dict that `inference` returns, here `ndvi` and `meta`. It writes the NDVI array to `result.tif` in the working directory and returns it as a `Raster` named `result`. The output has one `float32` band, so the code sets `dtype` and `count` in `meta`. The runner uploads the file in `value` after `postprocess` returns.

```python
async def postprocess(self, ndvi: Any, meta: Any) -> Dict[str, datatypes.Data]:  # type: ignore
    # perform any post-processing
    self.logger.info("In postprocessing")
    assert ndvi is not None
    meta.update(dtype="float32", count=1)
    with rasterio.open("result.tif", "w+", **meta) as rst:
        rst.write(ndvi.astype("float32"), 1)

    return {
        "result": datatypes.Raster(name="result",  value="result.tif"),
    }
```

??? Block
    The complete `ndvi/block.py`:

    ```python
    from typing import Any, Dict, List
    import rasterio
    import datatypes
    import clay
    from clay.core import BlockWrapper
    class Ndvi(BlockWrapper):
        def setup(self, bands: List[str]) -> None:  # type: ignore
            self.bands = bands

        async def preprocess(  # type: ignore
            self,
            raster: datatypes.Raster
        ) -> Dict[str, Any]:
            self.logger.warning(
                "In pre-process. Use self.logger for all logging. Avoid print statements"
            )
        
            if raster.properties.collection != "sentinel-s2-l2a-cogs":
                clay.failure(f"unsupported collection: {raster.properties.collection!r}")
            self.logger.info("preprocess has been completed, moving on to inference")
            return {"raster": raster}

        async def inference(self, raster: datatypes.Raster) -> Dict[str, Any]:  # type: ignore
            raster_value = rasterio.open(raster.value)
            required_bands = {}
            for bi in self.bands:
                self.logger.info(f"looking for band {bi} in raster band-list")
                idx = list(raster.properties.bands).index(bi)
                required_bands[bi] = raster_value.read(idx + 1).astype("float32")
            ndvi = (required_bands["B08"] - required_bands["B04"]) / (required_bands["B08"] + required_bands["B04"])
            self.logger.info(f"shape of calculated ndvi raster: {ndvi.shape}")
            self.logger.info("inference has been completed, moving on to postprocess")
            return {"ndvi": ndvi, "meta": raster_value.meta}

        async def postprocess(self, ndvi: Any, meta: Any) -> Dict[str, datatypes.Data]:  # type: ignore
            # perform any post-processing
            self.logger.info("In postprocessing")
            assert ndvi is not None
            meta.update(dtype="float32", count=1)
            with rasterio.open("result.tif", "w+", **meta) as rst: 
                rst.write(ndvi.astype("float32"), 1)
            return {
                "result": datatypes.Raster(name="result",  value="result.tif"),
            }

    ```



## Declare block specifications.
Declare the block's parameters, inputs and outputs in `clay.yaml` at the root of the project. Replace the generated `parameters`, `inputs` and `outputs` sections with the ones below.

1. `parameters`: passed to `setup()` to initialize the block. This block has one, `bands`.

    ```yaml
    parameters: # block initialization params
        - name: bands
          type: list
          default:
            - B04
            - B08
    ```
    **The argument names of `setup` need to match the parameter names in `clay.yaml`. Here the name is `bands`.**



2. `inputs`: passed to `preprocess`. This block has one, `raster`, of format `raster`.

    ```yaml
    inputs:
        - name: raster
          format: raster
          type: url
          properties:
            collection: sentinel-s2-l2a-cogs
    ```
    **The argument names of `preprocess` need to match the input names. Here the name is `raster`.**



3. `outputs`: returned from `postprocess`. This block has one, `result`, of format `raster`.

    ```yaml
    outputs:
        - name: result
          format: raster
          type: url
          properties:
            collection: sentinel-s2-l2a-cogs
    ```
    **The `name` of each datatype returned from `postprocess` needs to match an output name in `clay.yaml`. Here the name is `result`.** The runner adds the output's `properties` from `clay.yaml` to the returned `Raster`; properties set in the block code take precedence.


## Define sample input.

`clay new` generates `tests/sample_block_inputs.json` with inputs for the template block. Replace its contents with the input for this block:

```json
[
    {
        "name": "raster",
        "type": "url",
        "format": "raster",
        "value": "s3://my-bucket/sentinel-2/latest_data.tiff",
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
            "collection": "sentinel-s2-l2a-cogs"
        }
    }
]
```

The `value` must be an `s3://` URL or a path to a file inside the container. Other URL schemes, such as `https://`, fail with `No storage provider available for protocol`. `clay run` does not mount local folders into the container, so a path on your machine does not work. Before `preprocess` runs, the runner downloads the file to `<LOCAL_ARTIFACT_DOWNLOAD_PATH>/raster/` (default `/tmp/inputs/raster/`), so `raster.value` is a local path in your block code. See [LOCAL_ARTIFACT_DOWNLOAD_PATH](env-requirements.md#5-local_artifact_download_path).

!!! note
    A raster input can also have a `stac_url`: the `http://` or `https://` URL of a [STAC](https://stacspec.org/en) item, or the path to an item JSON file inside the container. The runner downloads only the item's JSON, saves it as `stac.json` next to the downloaded input, and sets `stac_url` to that local path. It does not download the imagery that the item links to, so this block still needs `value`.

## Build block in docker image

The block imports `rasterio`, which the base image does not include. Add it to `requirements.txt`:

```text
rasterio
```

Then build the image in the project folder:

```bash
clay build
```

The image is tagged `<name>:<version>` from `clay.yaml`, here `ndvi:v0.0.1`. Use `--tag` to choose another tag.

## Run the block locally

The input file is on S3, so pass AWS credentials to the container with `-e`. `clay run` passes only the variables given with `-e`; it does not mount `~/.aws` or any other folder. Run it in the project folder:

```bash
clay run -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... --input "$(cat tests/sample_block_inputs.json)"
```

Without an image name, `clay run` runs `ndvi:v0.0.1`, the image that `clay build` made. For temporary credentials, also pass `-e AWS_SESSION_TOKEN=...`. To set the region, pass `-e AWS_DEFAULT_REGION=...`. `-e NAME` without a value passes the value of `NAME` from your shell, as with `docker run`.

The block logs one JSON object per line. The log level is `DEBUG`, so the log includes a `WARNING` line, `Using existing logger without re-initialising.`, when the block is created, and `DEBUG` lines with each callback and its payload. The `Processing item` line is printed by the runner, not logged. The output looks like this (callback payloads and errors are shortened):

```text
🧐 Searching image ndvi:v0.0.1
Using configuration located at: /clay.yaml
{"level": "INFO", "timestamp": "2026-11-24T07:52:00.644313Z", "logger": "Ndvi", "loc": "runner.py:start:351", "message": "\ud83c\udfac starting clay job runner version: 1.5.0"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:00.644827Z", "logger": "Ndvi", "loc": "runner.py:_init_block:190", "message": "initializing block constructor"}
{"level": "WARNING", "timestamp": "2026-11-24T07:52:00.647785Z", "logger": "Ndvi", "loc": "logger.py:ClayLogger:238", "message": "Using existing logger without re-initialising."}
{"level": "DEBUG", "timestamp": "2026-11-24T07:52:00.647984Z", "logger": "Ndvi", "loc": "core.py:run_setup:78", "message": "Setting environment variable SAMPLE_ENV from config"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:00.648065Z", "logger": "Ndvi", "loc": "runner.py:_init_block:192", "message": "initializing block constructor completed"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:00.648125Z", "logger": "Ndvi", "loc": "runner.py:_collect_inputs:211", "message": "parsing inputs"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:00.651231Z", "logger": "Ndvi", "loc": "runner.py:_collect_inputs:218", "message": "processing input artifacts..."}
Processing item: raster with source path: s3://my-bucket/sentinel-2/latest_data.tiff
{"level": "INFO", "timestamp": "2026-11-24T07:52:00.657537Z", "logger": "Ndvi", "loc": "runner.py:_collect_inputs:221", "message": "\u2705 processing input artifacts completed"}
{"level": "DEBUG", "timestamp": "2026-11-24T07:52:00.658314Z", "logger": "Ndvi", "loc": "http_callback.py:_log:69", "message": "Sending callback to http://localhost:3000/callback"}
{"level": "DEBUG", "timestamp": "2026-11-24T07:52:00.658395Z", "logger": "Ndvi", "loc": "http_callback.py:_log:69", "message": "Callback payload: {\"data\": {\"id\": \"default_execution_id\", \"inputs\": [...], \"progress\": 0, \"start_time\": \"2026-11-24T07:52:00.644807+00:00\", \"metadata\": {}, \"status\": \"inprogress\"}}"}
{"level": "ERROR", "timestamp": "2026-11-24T07:52:01.869993Z", "logger": "Ndvi", "loc": "http_callback.py:_log:69", "message": "Error sending callback: HTTPConnectionPool(host='localhost', port=3000): Max retries exceeded with url: /callback (...)"}
{"level": "WARNING", "timestamp": "2026-11-24T07:52:01.870456Z", "logger": "Ndvi", "loc": "block.py:preprocess:14", "message": "In pre-process. Use self.logger for all logging. Avoid print statements"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:01.870520Z", "logger": "Ndvi", "loc": "block.py:preprocess:20", "message": "preprocess has been completed, moving on to inference"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:01.875484Z", "logger": "Ndvi", "loc": "block.py:inference:27", "message": "looking for band B04 in raster band-list"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:01.876818Z", "logger": "Ndvi", "loc": "block.py:inference:27", "message": "looking for band B08 in raster band-list"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:01.876965Z", "logger": "Ndvi", "loc": "block.py:inference:31", "message": "shape of calculated ndvi raster: (1390, 2834)"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:01.877000Z", "logger": "Ndvi", "loc": "block.py:inference:32", "message": "inference has been completed, moving on to postprocess"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:01.877090Z", "logger": "Ndvi", "loc": "block.py:postprocess:37", "message": "In postprocessing"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:01.879680Z", "logger": "Ndvi", "loc": "runner.py:success:224", "message": "sending callback for success"}
{"level": "DEBUG", "timestamp": "2026-11-24T07:52:01.879915Z", "logger": "Ndvi", "loc": "http_callback.py:_log:69", "message": "Sending callback to http://localhost:3000/callback"}
{"level": "DEBUG", "timestamp": "2026-11-24T07:52:01.879959Z", "logger": "Ndvi", "loc": "http_callback.py:_log:69", "message": "Callback payload: {\"data\": {\"id\": \"default_execution_id\", \"outputs\": [...], \"progress\": 100, \"start_time\": \"2026-11-24T07:52:00.644807+00:00\", \"end_time\": \"2026-11-24T07:52:01.879825+00:00\", \"metadata\": {}, \"status\": \"completed\"}}"}
{"level": "ERROR", "timestamp": "2026-11-24T07:52:03.090005Z", "logger": "Ndvi", "loc": "http_callback.py:_log:69", "message": "Error sending callback: HTTPConnectionPool(host='localhost', port=3000): Max retries exceeded with url: /callback (...)"}
{"level": "INFO", "timestamp": "2026-11-24T07:52:03.092454Z", "logger": "Ndvi", "loc": "runner.py:_create_output_json_files:293", "message": "Created output spec file: /tmp/clay/outputs/result/spec.json"}
```

The `Error sending callback` lines are expected when no orchestrator listens on `CALLBACK_ENDPOINT`; see [`CALLBACK_ENDPOINT`](env-requirements.md#10-callback_endpoint).

The runner copies each output file to `$REMOTE_OUTPUT_PATH/<output name>/`. The default `REMOTE_OUTPUT_PATH` is `/tmp/clay/outputs`, so here the result is at `/tmp/clay/outputs/result/result.tif` inside the container. `clay run` removes the container when it exits, so to keep the result, set an S3 location, for example `-e REMOTE_OUTPUT_PATH=s3://my-bucket/ndvi-outputs/`. See [REMOTE_OUTPUT_PATH](env-requirements.md#6-remote_output_path).

## Next Steps

Once your block is built and tested locally, you can:

- **Publish to Registry**: Use `clay publish` to push the image and register the block in a Clay registry
- **Deploy**: Run the image as a job on your platform; see [Deployment to Your Platform](getting-started.md#deployment-to-your-platform)
