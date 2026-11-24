---
title: Block Development Tutorial
order: 9
---

# Block Development
Welcome to our tutorial on creating an NDVI block for Sentinel-2 imagery using Clay.

## Prerequisite

Before diving in, ensure you have:

* Set up the project and completed the initial setup as per the instructions in the [Getting Started](getting-started.md) section.
* Familiarity with [Types](IO.md) and the [Block Specification Format](spec.md).



## Development

Block development in clay is divided into 4 parts

1. `setup`: Downloads weights and initializes the block.
2. `preprocess`: Preprocesses block inputs if required or do the any validation check which is required for the block input.
3. `inference`: Contains the block's algorithm for inference.
4. `postprocess`: Performs post-processing on the block output if required.

Clay will generate a class with the above mentioned methods you just need to use them for your block development.

### 1. Define the setup() method.

Our block requires defining the list of bands used for NDVI calculation.

```python
def setup(self, bands: List[str]) -> None:  # type: ignore
        self.bands = bands
```

### 2. Define `preprocess()` method.

1. This method takes a raster as input, which is of type Raster defined in the types.
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

This method will take the return value of `preprocess` as input. In this method we will define the actual algorithm for block development and return the expected output, here will return the calculated ndvi and the meta value of raster. rasterio band indexes start at 1, so the code reads band `idx + 1`. The bands are converted to `float32` before the division.

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
This method will take the return value of `inference` as input. Here we are taking `ndvi` and `meta` as input returned from `inference`. We will create a tif file which will show the ndvi output on the input raster. The output has one `float32` band, so the code sets `dtype` and `count` in `meta`.
    
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
    This is how the block.py will look now

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
Once you are done with the block implementation using the above defined interface, you should define your block input/output in `clay.yaml` file generated at the root of your project.

1. `parameters` which is being passed to the setup() to initialize you block named `bands`

    ```yaml
    parameters: # block initialization params
        - name: bands
          type: list
          default:
            - B04
            - B08
    ```
    **Input name in the `setup` function needs to match the parameter name in the spec file. For e.g we have used name `bands`**



2. `inputs` to you block which are being passed to `preprocess` named `raster` of type Raster.

    ```yaml
    inputs:
        - name: raster
          format: raster
          type: url
          properties:
            collection: sentinel-s2-l2a-cogs
    ```
    **Input name in the `preprocess` function needs to match input name from spec file. For e.g. we have used name `raster`**



3. `outputs` from your block which is being returned from `postprocess` names `result` of type Raster.

    ```yaml
    outputs:
        - name: result
          format: raster
          type: url
          properties:
            collection: sentinel-s2-l2a-cogs
    ```
    **The `name` of each datatype returned from `postprocess` needs to match an output name in the spec file. For e.g. we have used name `result`**


## Define sample input.

Clay generates the sample input file for us, which we will need to update with the correct input format. The file is `tests/sample_block_inputs.json`

Now we will define the input for the above defined block and use this file for testing the block.

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

!!! note
    You can also use the `stac_url` field instead of `value` if you want to provide a [STAC](https://stacspec.org/en) collection as input.

The `value` must be a path the container can read. `clay run` does not mount local folders into the container, so a path on your machine will not work. Use a remote URL such as `s3://`, or a path to a file inside the image. The runner downloads the file before `preprocess` runs, so `raster.value` is a local path in your block code.

## Build block in docker image

The block imports `rasterio`, which the base image does not include. Add it to `requirements.txt`:

```text
rasterio
```

```bash
clay build --tag ndvi:latest
```

Without `--tag`, the image is tagged `<name>:<version>` from `clay.yaml`.

## Run the block locally

Run the block using `clay run`:

```bash
clay run ndvi:latest --input "$(cat tests/sample_block_inputs.json)"
```

The input file is on S3, so pass AWS credentials to the container with `-e`, for example `-e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=...`.

The block logs one JSON object per line. The output will look something like this (shortened):

```shell
🧐 Searching image ndvi:latest
Using configuration located at: /clay.yaml
{"level": "INFO", "timestamp": "2026-11-23T07:16:32.006855Z", "logger": "Ndvi", "loc": "runner.py:start:351", "message": "\ud83c\udfac starting clay job runner version: 1.5.0"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:32.007011Z", "logger": "Ndvi", "loc": "runner.py:_init_block:190", "message": "initializing block constructor"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:32.009001Z", "logger": "Ndvi", "loc": "runner.py:_init_block:192", "message": "initializing block constructor completed"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:32.009025Z", "logger": "Ndvi", "loc": "runner.py:_collect_inputs:211", "message": "parsing inputs"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:32.041819Z", "logger": "Ndvi", "loc": "runner.py:_collect_inputs:218", "message": "processing input artifacts..."}
Processing item: raster with source path: s3://my-bucket/sentinel-2/latest_data.tiff
{"level": "INFO", "timestamp": "2026-11-23T07:16:32.048098Z", "logger": "Ndvi", "loc": "runner.py:_collect_inputs:221", "message": "\u2705 processing input artifacts completed"}
{"level": "WARNING", "timestamp": "2026-11-23T07:16:33.264982Z", "logger": "Ndvi", "loc": "block.py:preprocess:14", "message": "In pre-process. Use self.logger for all logging. Avoid print statements"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:33.265132Z", "logger": "Ndvi", "loc": "block.py:preprocess:20", "message": "preprocess has been completed, moving on to inference"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:33.292228Z", "logger": "Ndvi", "loc": "block.py:inference:27", "message": "looking for band B04 in raster band-list"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:33.293657Z", "logger": "Ndvi", "loc": "block.py:inference:27", "message": "looking for band B08 in raster band-list"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:33.293827Z", "logger": "Ndvi", "loc": "block.py:inference:31", "message": "shape of calculated ndvi raster: (1390, 2834)"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:33.293872Z", "logger": "Ndvi", "loc": "block.py:inference:32", "message": "inference has been completed, moving on to postprocess"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:33.293972Z", "logger": "Ndvi", "loc": "block.py:postprocess:37", "message": "In postprocessing"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:33.333068Z", "logger": "Ndvi", "loc": "runner.py:success:224", "message": "sending callback for success"}
{"level": "INFO", "timestamp": "2026-11-23T07:16:34.549203Z", "logger": "Ndvi", "loc": "runner.py:_create_output_json_files:293", "message": "Created output spec file: /tmp/clay/outputs/result/spec.json"}
```

The runner copies each output file to `$REMOTE_OUTPUT_PATH/<output name>/`. The default `REMOTE_OUTPUT_PATH` is `/tmp/clay/outputs`, so here the result is at `/tmp/clay/outputs/result/result.tif` inside the container. `clay run` removes the container when it exits, so to keep the result, set an S3 location, for example `-e REMOTE_OUTPUT_PATH=s3://my-bucket/ndvi-outputs/`. See [REMOTE_OUTPUT_PATH](env-requirements.md#6-remote_output_path).

## Next Steps

Once your block is built and tested locally, you can:

- **Publish to Registry**: Use `clay publish` to push your block to the Clay registry
- **Deploy**: Deploy your block to your infrastructure or orchestrator
