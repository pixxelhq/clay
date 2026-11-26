---
title: Getting Started
order: 2
---

# Getting Started

This guide walks you through installing Clay and creating your first block project.

## Components of Clay

Clay ships as two complementary pieces that you'll work with throughout this guide:

* **Clay CLI** — A Go command-line tool used to scaffold projects, build container images, and interact with a registry.
* **Clay Python SDK** — A runtime library imported by your block code; it provides the `BlockWrapper` base class and handles the execution lifecycle, I/O, and storage abstractions.

The typical workflow is: scaffold and build with the **CLI**, implement your block logic against the **Python SDK**, and (optionally) publish the result to a registry with the CLI.

> **What You'll Learn**
>
> * Installing the Clay CLI
> * Creating a Clay project
> * Building and testing your block locally
> * Publishing to a Registry

## Prerequisite
* **A macOS or Linux shell**: the commands in this guide are written for macOS and Linux shells.
* **Docker**: Docker should be [installed](https://docs.docker.com/get-docker/) in your system. It will be used to build image and create container. `clay` runs `docker` as your user, so Docker must work without `sudo`. This is the default with Docker Desktop and rootless Docker; on Linux, add your user to the `docker` group ([post-install steps](https://docs.docker.com/engine/install/linux-postinstall/)).
* **python**: You should have python >=3.10 installed in your system

## Install clay CLI

Pick whichever installation method is most convenient.

### Option 1 — Homebrew (macOS / Linux, recommended)

```shell
brew tap pixxelhq/tap
brew install clay --formula
```

### Option 2 — Download a pre-built binary

Download the archive for your platform from
[GitHub Releases](https://github.com/pixxelhq/clay/releases) and move the
`clay` binary onto your `PATH`. Set `VERSION` to the latest release, without
the "v":

```shell
VERSION=1.5.0

# macOS (Apple Silicon)
curl -L https://github.com/pixxelhq/clay/releases/download/v${VERSION}/clay_${VERSION}_darwin_arm64.tar.gz | tar -xz clay

# Linux (amd64)
curl -L https://github.com/pixxelhq/clay/releases/download/v${VERSION}/clay_${VERSION}_linux_amd64.tar.gz | tar -xz clay

sudo mv clay /usr/local/bin/
```

Archives are named `clay_<version>_<os>_<arch>.tar.gz` and are published for macOS, Linux and Windows on `amd64` and `arm64`.

### Option 3 — Build from source

Requires Go 1.22+.

```shell
git clone https://github.com/pixxelhq/clay.git
cd clay
go build -o clay .
sudo mv clay /usr/local/bin/
```

`make go-binaries` builds the CLI for every platform into `./bin/`, with the version and platform in each file name.

### Verify installation

```shell
clay --version
```

## Create Your First Block

### Create Project Structure

Create a project for a block named `my-block`. The following command creates the project in the directory `./my-block`, and uses the last part of the path as the block name (pass `--name` to choose another):

```shell
clay new my-block
```

If the directory already holds files, such as a repository with your model code, run `clay init` in it instead. `clay init` keeps the files that are already there and stops if the directory already has a `clay.yaml` (use `--force` to write the template anyway). It does not run in the filesystem root, your home folder, or the `Desktop`, `Documents` and `Downloads` folders in it. See [CLI Reference](cli-reference.md#init).

Navigate into the project directory:
```shell
cd my-block
```

### Understanding the Generated Project Structure

Clay generates a minimal project with the files every block needs to develop, test, and deploy it. Here's what each file and directory does:

```
my-block/
├── my_block/                    # Block package (the block name in snake_case)
│   ├── block.py                 # Your block implementation (BlockWrapper)
│   └── entry.py                 # Block entry point (don't modify)
├── tests/
│   ├── test_block.py            # Local testing script
│   └── sample_block_inputs.json # Example inputs for testing
├── clay.yaml                    # Clay configuration
├── requirements.txt             # Runtime dependencies, installed in the image
├── requirements-dev.txt         # Development tools (ruff, pytest, ...); never installed in the image
├── pyproject.toml               # Python project configuration
├── .gitignore                   # Git ignore rules
├── .dockerignore                # Files left out of the Docker build context (.venv, caches, tests, .git)
└── README.md                    # How to set up, test, build and run the block
```

The Dockerfile that `clay build` generates copies only the file in `build.requirements`, the block package folder and `clay.yaml` into the image.

Add optional files with `--with` (see [CLI Reference](cli-reference.md#new)):

* `--with catalog` — `catalog.yaml`, to describe the block in a catalog
* `--with conda` — `conda.yaml`, and `clay.yaml` set to build with conda (recommended for GPU blocks)
* `--with pre-commit` — `.pre-commit-config.yaml` with ruff, ruff-format and basic file checks, and `pre-commit` in `requirements-dev.txt`

Set up a virtual environment and install the development tools:

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

#### Key Files Explained

<details markdown="1">
<summary><strong>block.py</strong> — your block implementation</summary>

This is where you write your block logic. A shortened version of the generated file:

```python
from typing import Any, Dict

import datatypes as T
from clay.core import BlockWrapper


class MyBlock(BlockWrapper):
    def setup(self, weight: int, **kwargs) -> None:
        self.weight = weight

    async def preprocess(self, input1: T.String, input2: T.Number) -> Dict[str, Any]:
        self.logger.info(f"Preprocessing: input1={input1.value}, input2={input2.value}")
        return {"input1": input1, "input2": input2}

    async def inference(self, input1: T.String, input2: T.Number) -> Dict[str, Any]:
        return {"result": input2.value * self.weight}

    async def postprocess(self, result: int) -> Dict[str, T.Data]:
        return {"output1": T.Number(name="output1", value=str(result))}
```

> **How the methods connect to `clay.yaml`**
>
> * `setup` runs once, when the block is created. It gets the `default` of each entry in `parameters` as a keyword argument.
> * `preprocess` gets one keyword argument for each item in the input JSON, named by the item's `name`. Name its arguments after the `inputs` in `clay.yaml`. A missing or unexpected argument fails the run with `TypeError`.
> * `preprocess` and `inference` return a dict. Its keys are the argument names of the next method.
> * `postprocess` returns a dict of datatypes, such as `T.Number(...)`. The `name` of each datatype must match an output in `clay.yaml`, or the run fails with `KeyError`. The dict keys are not checked, and an output that is declared but not returned is not an error.
> * Clay does not compare the format or type of an input or output with `clay.yaml`. Before `preprocess`, it checks only the `validation` rules of string, number and date inputs.

</details>

<details markdown="1">
<summary><strong>clay.yaml</strong> — configuration file</summary>

Defines your block's grammar and dependency requirements. An excerpt of the generated file:

```yaml
name: my-block
version: v0.0.1

parameters:  # Setup parameters
  - name: weight
    type: int
    default: 5

inputs:      # Block inputs
  - name: input1
    format: string
    type: str

  - name: input2
    format: number
    type: int

outputs:     # Block outputs
  - name: output1
    format: number
    type: int

build:       # Build configuration
  python-version: "3.10"
  gdal: true             # base image with GDAL installed
  requirements: requirements.txt

gpu: false   # Set to true for GPU blocks
```

</details>

<details markdown="1">
<summary><strong>README.md</strong> — block documentation</summary>

How to set up, test, build and run the block. Add what the block does, its inputs and outputs, and its parameters for the people who use it.

</details>

**Where to start:**

1. **Edit `my_block/block.py`** — Implement your block logic
2. **Update `clay.yaml`** — Define inputs, outputs, and requirements
3. **Modify `tests/sample_block_inputs.json`** — Add realistic test data

**Files you won't need to modify:**

* `my_block/entry.py` — Clay's block entry point

> **Setup Complete!** Your project is ready for development.

## Build and Test Your Block

Build and test the block locally.

* **Configure Dependencies**

    Update the `build.requirements` field in `clay.yaml` to specify your dependency manager file. By default, it is set to `requirements.txt`. To install packages with conda, set `build.conda: true` and `build.requirements: conda.yaml`, or create the project with `clay new <path> --with conda`.

    Put only what the block needs at runtime in `requirements.txt`; it is installed in the image. It lists `pixxel-clay` and `pixxel-datatypes` without versions. `pixxel-clay` has no version because the image gets the version of the `clay` CLI that builds it. Do not add a version to it, or the build fails after a CLI upgrade. To use the same version locally, run `pip install pixxel-clay==<version>` with the version from `clay --version`. Development tools go in `requirements-dev.txt`, which starts with `-r requirements.txt` and is never installed in the image. For local development, run `pip install -r requirements-dev.txt`.

    > **GPU Blocks**
    >
    > If your block uses GPU, set `gpu: true` in `clay.yaml`, so that the block runs with GPUs. To install packages with conda instead of pip, set `build.conda: true` and point `build.requirements` to a `conda.yaml`; Clay creates a conda environment from it. See [build](spec.md#build).

* **Build the Docker Image**

    ```shell
    clay build
    ```
    Run it in the project folder. This generates a Dockerfile from `clay.yaml` and builds an image named after the `name` and `version` in `clay.yaml`. For example, if the `name` is `my-block` and the `version` is `v0.0.1`, the image is `my-block:v0.0.1`.

    **Common flags:**

    - `-t, --tag`: Build tag in the format `repository:tag`. Default: `<name>:<version>` from `clay.yaml`.
    - `-f, --file`: Dockerfile path. Without it, Clay uses `./Dockerfile` if it exists, or generates one from `clay.yaml` on each build. To customize it, run `clay dockerfile > Dockerfile`, edit it, and build with `clay build -f Dockerfile`.

    `--no-cache`, `--secret`, `--build-arg` and `--platform` are passed to the Docker build; see [CLI Reference](cli-reference.md#build).

* **Test without Docker**

    ```shell
    python tests/test_block.py
    ```

    This runs the block in your virtual environment with the inputs in `tests/sample_block_inputs.json`. `pytest` runs the same test. It uses the same defaults as the image, so it writes inputs and outputs under `/tmp` and logs `Error sending callback` lines (see the note below).

* **Run Locally**

    ```shell
    clay run --input "$(cat tests/sample_block_inputs.json)"
    ```

    Run it in the project folder: `clay run` reads `clay.yaml`. Without an image name, it runs `<name>:<version>` from `clay.yaml`, the image that `clay build` made.

    The block prints `Using configuration located at: /clay.yaml`, then one JSON log line per event. The log level is `DEBUG`, so the lines include:

    * the runner's own steps, such as `initializing block constructor` and `parsing inputs`;
    * one `WARNING` line, `Using existing logger without re-initialising.`, when the block is created. It is expected; see [Logging](logging.md#where-logs-go);
    * `DEBUG` lines with each callback sent to `CALLBACK_ENDPOINT` and its payload;
    * your block's own log lines.

    The last lines look like this (the callback payload and the error message are shortened):
    ```
    {"level": "INFO", "timestamp": "2026-11-24T07:48:22.468035Z", "logger": "MyBlock", "loc": "block.py:preprocess:69", "message": "Preprocessing: input1=starting-point, input2=5"}
    {"level": "INFO", "timestamp": "2026-11-24T07:48:22.468246Z", "logger": "MyBlock", "loc": "block.py:inference:85", "message": "Running inference"}
    {"level": "INFO", "timestamp": "2026-11-24T07:48:22.468430Z", "logger": "MyBlock", "loc": "block.py:postprocess:108", "message": "Postprocessing: result=25"}
    {"level": "INFO", "timestamp": "2026-11-24T07:48:22.469237Z", "logger": "MyBlock", "loc": "runner.py:success:224", "message": "sending callback for success"}
    {"level": "DEBUG", "timestamp": "2026-11-24T07:48:22.470025Z", "logger": "MyBlock", "loc": "http_callback.py:_log:69", "message": "Sending callback to http://localhost:3000/callback"}
    {"level": "DEBUG", "timestamp": "2026-11-24T07:48:22.470179Z", "logger": "MyBlock", "loc": "http_callback.py:_log:69", "message": "Callback payload: {\"data\": {\"id\": \"default_execution_id\", \"outputs\": [...], \"progress\": 100, \"start_time\": \"2026-11-24T07:48:21.241344+00:00\", \"end_time\": \"2026-11-24T07:48:22.469641+00:00\", \"metadata\": {}, \"status\": \"completed\"}}"}
    {"level": "ERROR", "timestamp": "2026-11-24T07:48:23.687763Z", "logger": "MyBlock", "loc": "http_callback.py:_log:69", "message": "Error sending callback: HTTPConnectionPool(host='localhost', port=3000): Max retries exceeded with url: /callback (...)"}
    {"level": "INFO", "timestamp": "2026-11-24T07:48:23.690299Z", "logger": "MyBlock", "loc": "runner.py:_create_output_json_files:293", "message": "Created output spec file: /tmp/clay/outputs/output1/spec.json"}
    ```

    > **Note:** `Error sending callback` lines for `localhost:3000` are expected when running locally. The callback is only used when an orchestrator runs the block; see [`CALLBACK_ENDPOINT`](env-requirements.md#10-callback_endpoint).



## Publishing to Registry (Optional)

Once you've developed and tested your block locally, you can publish different
versions of your block to a **Clay registry** — a service that tracks block
versions, metadata, and deployment information.

A registry is optional. You can always build and run block containers without
one.

> **Self-hosting the registry**
>
> Clay ships with a registry implementation that you can run on your own
> infrastructure or locally during development. See [Clay Registry](registry.md)
> for setup instructions, including running the service locally with
> `make build && make run` from the `registry/` directory. You can also point
> the CLI at any compatible registry instance.

* **Update Version**

    Update the version in `clay.yaml` before publishing:
    ```yaml
    version: v1.0.0  # Follow semantic versioning
    ```

* **Publish to Registry**

    ```shell
    clay publish
    ```

    **Available Flags**:

    - `--docker-registry` *(required unless `CLAY_DOCKER_REGISTRY` is set)* - Docker image registry to push to
    - `--clay-registry` *(required unless `CLAY_REGISTRY_HOST` is set)* - Clay block registry URL
    - `--catalog-url` *(optional)* - URL of the published `catalog.yaml` (see `clay block assets upload-catalog`)
    - `-f, --file` *(optional)* - Dockerfile to build with, as in `clay build`

    **Example with custom registries:**

    ```shell
    clay publish --clay-registry https://clay.example.com --docker-registry registry.example.com
    ```

* **List Available Blocks**

    ```shell
    clay block list --clay-registry https://clay.example.com
    ```

    Sample output (the CLI prints a JSON array of blocks):
    ```json
    [
      {
        "id": "uuid-here",
        "name": "my-block",
        "kind": "block",
        "type": "processing",
        "version": "v1.0.0",
        "docker_image": "registry-url/my-block:v1.0.0"
      },
      {
        "id": "another-uuid",
        "name": "another-block",
        "kind": "block",
        "type": "processing",
        "version": "v0.2.0",
        "docker_image": "registry-url/another-block:v0.2.0"
      }
    ]
    ```

* **Describe Block Version**

    ```shell
    clay block describe my-block --version v1.0.0 --clay-registry https://clay.example.com
    ```

    Sample output (`specification` is shortened):
    ```json
    {
      "id": "uuid-here",
      "name": "my-block",
      "kind": "block",
      "type": "processing",
      "version": "v1.0.0",
      "docker_image": "registry-url/my-block:v1.0.0",
      "specification": {
        "parameters": [{"name": "weight", "type": "int", "default": 5}],
        "inputs": [{"name": "input1", "format": "string", "type": "str"}],
        "outputs": [{"name": "output1", "format": "number", "type": "int"}]
      }
    }
    ```

### Deployment to Your Platform

You can deploy your block container to any orchestration platform — publishing
to a registry is optional and only required if you want centralized version
tracking.

Clay blocks are batch workloads: the container reads its inputs, runs once and
exits. It does not start an HTTP server. Run it as a job:

* **Kubernetes**: Jobs or CronJobs
* **Cloud services**: AWS Batch jobs or ECS tasks, Google Cloud Run jobs, Azure Container Instances
* **Custom Orchestrators**: Integrate with your platform using the Registry API


## Next Steps

Now that you have Clay set up, continue with:

* **[Clay Architecture Overview](overview.md)**: Understand clay architecture
* **[Block Specification](spec.md)**: Understand how to configure your block
* **[Input/Output & Datatypes](IO.md)**: Learn about Clay's type system
* **[Block Development Tutorial](block-development.md)**: Learn how to build your first block
