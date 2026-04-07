# Block Development
Welcome to our tutorial on creating an NDVI block for Landsat imagery using Clay.

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
2. It validates whether the given raster is from Landsat Sentinel.
3. If the validation fails, it calls Clay.failure(), which returns an error message for the end user.

```python
     async def preprocess(  # type: ignore
        self,
        raster: datatypes.Raster
    ) -> Dict[str, Any]:
        self.logger.warning(
            "In pre-process. Use self.logger for all logging. Avoid print statements"
        )
       
        if raster.Properties == None or raster.Properties.Collection != "sentinel-s2-l2a-cogs":
            clay.failure(f"unsupported collection: {raster.Properties.Collection}")
        self.logger.info("preprocess has been completed, moving on to inference")
        return {"raster": raster}
```

### 3. Define `inference()` method.

This method will take the return value of `preprocess` as input. In this method we will define the actual algorithm for block development and return the expected output, here will return the calculated ndvi and the meta value of raster.

```python
    async def inference(self, raster: datatypes.Raster) -> Dict[str, Any]:  # type: ignore
        raster_value = rasterio.open(raster.value)
        required_bands = {}
        for bi in self.bands:
            self.logger.info(f"looking for band {bi} in raster band-list")
            idx = raster.Properties.Bands.index(bi)
            required_bands[bi] = raster_value.read(idx)

        ndvi = (required_bands["B08"] - required_bands["B04"]) / (required_bands["B08"] + required_bands["B04"])
        self.logger.info(f"shape of calculated ndvi raster: {ndvi.shape}")
        self.logger.info("inference has been completed, moving on to postprocess")
        return {"ndvi": ndvi, "meta": raster_value.meta}
```

### 4. Define `postprocess` method.
This method will take the return value of `inference` as input. Here we are taking `ndvi` and `metda` as input returned from `inference`. We will create a tif file which will show the ndvi output on the input raster.
    
```python

    async def postprocess(self, ndvi: Any, meta: Any) -> Dict[str, datatypes.Data]:  # type: ignore
        # perform any post-processing
        self.logger.info("In postprocessing")
        assert ndvi is not None
        meta["dtype"] = "float32"
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
    import clay
    from clay.core import BlockWrapper
    from clay import types as datatypes
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
        
            if raster.Properties == None or raster.Properties.Collection != "sentinel-s2-l2a-cogs":
                clay.failure(f"unsupported collection: {raster.Properties.Collection}")
            self.logger.info("preprocess has been completed, moving on to inference")
            return {"raster": raster}

        async def inference(self, raster: datatypes.Raster) -> Dict[str, Any]:  # type: ignore
            raster_value = rasterio.open(raster.value)
            required_bands = {}
            for bi in self.bands:
                self.logger.info(f"looking for band {bi} in raster band-list")
                idx = raster.Properties.Bands.index(bi)
                required_bands[bi] = raster_value.read(idx)
            ndvi = (required_bands["B08"] - required_bands["B04"]) / (required_bands["B08"] + required_bands["B04"])
            self.logger.info(f"shape of calculated ndvi raster: {ndvi.shape}")
            self.logger.info("inference has been completed, moving on to postprocess")
            return {"ndvi": ndvi, "meta": raster_value.meta}

        async def postprocess(self, ndvi: Any, meta: Any) -> Dict[str, datatypes.Data]:  # type: ignore
            # perform any post-processing
            self.logger.info("In postprocessing")
            assert ndvi is not None
            meta["dtype"] = "float32"
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
     **Input name in the `postprocess` function needs to match input name from spec file. For e.g. we have used name `result`**


## Define sample input.

Clay generates the sample input file for us, which we will need to update with the correct input format. The file exists in the directory `./{Blockname}/sample_block_inputs.json`

Now we will define the input for the above defined block and use this file for testing the block.

```json
[
    {
        "name": "raster",
        "type": "url",
        "format": "raster",
        "value": "./latest_data.tiff",
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

We have a file `latest_data.tiff` on our local, you can give the path from where the raster will be taken as block input.

## Build block in docker image
Run `clay build`

The output will look something like

```shell
aws codeartifact get-authorization-token --domain REDACTED-ARTIFACTORY --domain-owner REDACTED-AWS-ACCT --query authorizationToken --region us-east-2 --output text > 
sudo DOCKER_BUILDKIT=1 docker build \
		--secret id=CODEARTIFACT_AUTH_TOKEN,src= \
		--build-arg AWS_ENV_PROFILE= \
		-t ndvi \
		-f Dockerfile \
		.
Password:
[+] Building 0.0s (0/1)                                                                                                                                                                             docker:defau[+] Building 4.3s (11/11) FINISHED                                                       docker:default
 => [internal] load .dockerignore                                                                  0.0s
 => => transferring context: 2B                                                                    0.0s
 => [internal] load build definition from Dockerfile                                               0.0s
 => => transferring dockerfile: 687B                                                               0.0s
 => [internal] load metadata for ghcr.io/osgeo/gdal:ubuntu-small-3.6.3                             4.2s
 => [stage-0 1/6] FROM ghcr.io/osgeo/gdal:ubuntu-small-3.6.3@sha256:bfa7915a3ef942b4f6f61223ee57e  0.0s
 => [internal] load build context                                                                  0.0s
 => => transferring context: 1.61kB                                                                0.0s
 => CACHED [stage-0 2/6] WORKDIR /app                                                              0.0s
 => CACHED [stage-0 3/6] RUN apt-get update &&     apt-get install -y python3.10 python3-pip wget  0.0s
 => CACHED [stage-0 4/6] COPY requirements.txt .                                                   0.0s
 => CACHED [stage-0 5/6] RUN --mount=type=secret,id=CODEARTIFACT_AUTH_TOKEN     CODEARTIFACT_AUTH  0.0s
 => CACHED [stage-0 6/6] COPY Ndvi /app                                                            0.0s
 => exporting to image                                                                             0.0s
 => => exporting layers                                                                            0.0s
 => => writing image sha256:8ee114042d7ee72c99bdab931ed2ecdafe46d2ea4a19efbcba439214f84ba984       0.0s
 => => naming to docker.io/library/ndvi                                                            0.0s

What's Next?
  View summary of image vulnerabilities and recommendations → docker scout quickview
/Library/Developer/CommandLineTools/usr/bin/make clean-secrets
rm 
```

## Run the block locally

Run the block using `clay run`:

```bash
clay run -e INPUT_JSON="$(cat sample_block_inputs.json)" ndvi:latest
```

The output will look something like:

```shell
Using configuration located at: /Users/xyz/work/example/blocks/NDVI/Ndvi/clay.yaml
WARNING - 2024-04-12 01:07:16,192 - runner.py:195 - job_block_runner - 'remote-prefix'
INFO - 2024-04-12 01:07:16,193 - core.py:346 - job_block_runner - Initializing Block...
INFO - 2024-04-12 01:07:16,195 - core.py:348 - job_block_runner - Block initialization complete.
WARNING - 2024-04-12 01:07:17,200 - core.py:372 - job_block_runner - `ORCHESTRATOR_URL` not set, and hence not firing callback
ERROR - 2024-04-12 01:07:17,200 - runner.py:403 - job_block_runner - Failed to fire callback
WARNING - 2024-04-12 01:07:17,202 - block.py:17 - Ndvi - In pre-process. Use self.logger for all logging. Avoid print statements
INFO - 2024-04-12 01:07:17,202 - block.py:23 - Ndvi - preprocess has been completed, moving on to inference
INFO - 2024-04-12 01:07:17,241 - block.py:30 - Ndvi - looking for band B04 in raster band-list
INFO - 2024-04-12 01:07:17,662 - block.py:30 - Ndvi - looking for band B08 in raster band-list
/Users/xyz/work/example/blocks/NDVI/Ndvi/block.py:34: RuntimeWarning: invalid value encountered in divide
  ndvi = (required_bands["B08"] - required_bands["B04"]) / (required_bands["B08"] + required_bands["B04"])
INFO - 2024-04-12 01:07:17,683 - block.py:35 - Ndvi - shape of calculated ndvi raster: (1390, 2834)
INFO - 2024-04-12 01:07:17,683 - block.py:36 - Ndvi - inference has been completed, moving on to postprocess
INFO - 2024-04-12 01:07:17,694 - block.py:41 - Ndvi - In postprocessing
INFO - 2024-04-12 01:07:17,949 - runner.py:260 - job_block_runner - copying file from `result.tif` to `runs/wf123/job123/task123/outputs/result/result.tif`
WARNING - 2024-04-12 01:07:18,006 - core.py:372 - job_block_runner - `ORCHESTRATOR_URL` not set, and hence not firing callback
WARNING - 2024-04-12 01:07:18,006 - runner.py:426 - job_block_runner - failed to fire callback successfully
INFO - 2024-04-12 01:07:18,006 - runner.py:470 - job_block_runner - results: [Raster(Format='raster', Type='url', Name='result', Value='runs/wf123/job123/task123/outputs/result/result.tif', Default=None, IsArtifact=True, Properties=RasterProperties(Bands=None, Source=None, Collection='sentinel-s2-l2a-cogs', Dtype=None))]
```

You can notice here that the output of the block has been generated at `runs/wf123/job123/task123/outputs/result/result.tif`

## Next Steps

Once your block is built and tested locally, you can:

- **Publish to Registry**: Use `clay publish` to push your block to the Clay registry
- **Deploy**: Deploy your block to your infrastructure or orchestrator

!!! info "Pixxel Users"
    For Pixxel-specific deployment workflows (GitHub Actions, Orchestrator integration, Platform platform), see [Pixxel Platform Integration](pixxel-integration.md).
