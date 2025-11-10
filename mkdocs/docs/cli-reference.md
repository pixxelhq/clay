## Description
---

The clay CLI tool for block/model related operations

---

### Clay Commands:

>  Get version of clay-cli

```shell
clay version
```

>   Get help with any command

```shell
clay <command> --help
```

---

### Model-related Available Command:

```shell
clay create <command>
```

#### Sub-commands

> Generate starter files for your model

```shell
clay create project <outputDir> <modelName>
```

> Creates a dockerfile to package and serve your model

```shell
clay create dockerfile <modelSpecificationPath> <sourceCodeFolder>
```

---

### Block-realated Available Command

> **Add a new block to orchestrator database**

```
clay add block <specFilePath> <flags>

available flags:
    -e, --env string   Environment to add new block to: dev, stg, prod (default "dev")
```
<br>

> **Get spec file for a particular block version**<br>
>   By Default only "released" block spec is provided
>   Set "status" flag to fetch "draft" and "disabled" block spec

```
clay get block <flags>

available flags:
    -n, --name string      Name of block
    -s, --status string    Status of block: draft, released, disabled (default "released")
    -v, --version string   Version of block
    -e, --env string       Environment to get block spec from: dev, stg, prod (default "dev")
```
<br>

>**List the blocks available in orchestrator database**<br>
>If blockname is provided, all available "released" blocks will be listed
>Use flags to list versions available for a block
>Set "status" flag to fetch "draft" and "disabled" block spec

```
clay list block <flags>

available flags:
    -n, --name string     Name of block
    -s, --status string   Possible status of block: draft, released, disabled (default "released")
    -e, --env string      Environment to list block in: dev, stg, prod (default "dev")
```
<br>

>**Update an existing block**<br>
>Specify the blockname, version and updated specfile path to update the block.<br>
>Use flag 'env' to specify the environment in which the block is to be updated.

```
clay update block <specFilePath> <flags>

available flags:
    -n, --name string      Name of block
    -s, --status string    Status of block: draft, released, disabled (default "released")
    -v, --version string   Version of block
    -e, --env string       Env in which block needs to be updated: dev, stg, prod (default "dev")
```
<br>

>**Upload the readme for the model to cloud**
```
clay upload readme <flags>

available flags:
    -n, --name string      Name of block as specified in spec file
    -v, --version string   Version of block
    -e, --env string       Environment to upload readme to: dev, stg, prod (default "dev")
```
<br>

>**Upload assets to cloud storage for a block**<br>
>Upload files or directories to cloud storage (S3, GCS, Azure) for a specific block.<br>
>Assets can be stored at the block name level (shared across versions) or version-specific.

```
clay block assets upload <path> <flags>

available flags:
    -n, --name string      Name of the block (required)
    -v, --version string   Version of the block (optional)
    --bucket string        Storage bucket name (required)
    --provider string      Storage provider: s3, gcs, azure (default "s3")
    --region string        Storage region (required for S3)
    --readme               Process markdown templates before upload
```
<br>

>**List assets stored for a block**<br>
>List all assets stored in cloud storage for a specific block and optionally version.

```
clay block assets list <flags>

available flags:
    -n, --name string      Name of the block (required)
    -v, --version string   Version of the block (optional)
    --bucket string        Storage bucket name (required)
    --provider string      Storage provider: s3, gcs, azure (default "s3")
    --region string        Storage region (required for S3)
```
<br>

>**Download a specific asset from block storage**<br>
>Download an asset file from cloud storage to your local filesystem.<br>
>If a version is specified, it will check version-specific assets first, then fall back to name-level assets.

```
clay block assets download <asset-path> <flags>

available flags:
    -n, --name string      Name of the block (required)
    -v, --version string   Version of the block (optional)
    -o, --output string    Local path to save the downloaded asset (default ".")
    --bucket string        Storage bucket name (required)
    --provider string      Storage provider: s3, gcs, azure (default "s3")
    --region string        Storage region (required for S3)
```
