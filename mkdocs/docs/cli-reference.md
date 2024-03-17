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
