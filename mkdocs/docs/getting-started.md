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
* **macOS or Linux**: `clay` CLI is supported in macOS and Linux.
* **Docker**: Docker should be [installed](https://docs.docker.com/get-docker/) in your system. It will be used to build image and create container.
* **python**: You should have python >=3.10 installed in your system

## Install clay CLI

Pick whichever installation method is most convenient.

### Option 1 — Download a pre-built binary (recommended)

Download the latest release for your platform from
[GitHub Releases](https://github.com/pixxelhq/clay/releases) and move it onto
your `PATH`:

```shell
# macOS (Apple Silicon)
curl -L https://github.com/pixxelhq/clay/releases/latest/download/clay-<version>-macosx-arm64 -o /usr/local/bin/clay
chmod +x /usr/local/bin/clay

# Linux (amd64)
curl -L https://github.com/pixxelhq/clay/releases/latest/download/clay-<version>-linux-amd64 -o /usr/local/bin/clay
chmod +x /usr/local/bin/clay
```

Binaries are published for macOS (amd64, arm64), Linux (amd64, arm64), and Windows (amd64).

### Option 2 — Homebrew (macOS / Linux)

> **Coming soon**
>
> A Homebrew formula is on the roadmap. Once published, you'll be able to install Clay with:
>
> ```shell
> brew install clay
> ```
>
> Until then, please use the pre-built binaries above or build from source.

### Option 3 — Build from source

Requires Go 1.22+.

```shell
git clone https://github.com/pixxelhq/clay.git
cd clay
make go-binaries        # output goes to ./bin/
```

### Verify installation

```shell
clay --version
```

## Create Your First Block

### Create Project Structure

Let's create a project for a block named `MyBlock`. The following command creates the project in the current directory by default. You can specify a different directory path instead of `.`

```shell
clay new . MyBlock
```

Navigate into the project directory:
```shell
cd MyBlock
```

### Understanding the Generated Project Structure

Clay generates a complete project scaffolding with everything you need to develop, test, and deploy your block. Here's what each file and directory does:

```
MyBlock/
├── src/                         # Main source code directory
│   ├── block.py                 # Your block implementation (BlockWrapper)
│   └── entry.py                 # Block entry point (don't modify)
├── tests/
│   ├── test_block.py            # Local testing script
│   └── sample_block_inputs.json # Example inputs for testing
├── catalog.yaml                 # Marketplace documentation (media + content sections)
├── clay.yaml                    # Clay configuration
├── requirements.txt / conda.yaml # Python dependencies — pip (default) or conda (recommended for GPU blocks)
├── Makefile                     # Common commands
├── pyproject.toml               # Python project configuration
├── .pre-commit-config.yaml      # Pre-commit hooks
├── .gitignore                   # Git ignore rules
└── README.md                    # Project README
```

#### Key Files Explained

<details markdown="1">
<summary><strong>block.py</strong> — your block implementation</summary>

This is where you write your actual block logic:

```python
from clay.core import BlockWrapper
import datatypes

class MyBlock(BlockWrapper):
    def setup(self, **parameters):
        # Initialize block (load weights, configure, etc.)
        pass

    async def preprocess(self, **inputs):
        # Prepare and validate inputs
        return processed_data

    async def inference(self, **processed_data):
        # Run block predictions
        return predictions

    async def postprocess(self, **predictions):
        # Format outputs according to specification
        return formatted_outputs
```

> **Important — Match the contract in `clay.yaml`**
>
> The `preprocess`, `inference`, and `postprocess` methods must accept and
> return values whose names and types match the `inputs` and `outputs`
> declared in `clay.yaml`. The runner uses the spec to validate I/O at
> runtime, so a mismatch will cause execution to fail.

</details>

<details markdown="1">
<summary><strong>clay.yaml</strong> — configuration file</summary>

Defines your block's grammar and dependency requirements:

```yaml
name: myblock
version: v0.0.1

parameters:  # Setup parameters
  - name: weight
    type: int
    default: 5

inputs:      # Block inputs
  - name: input1
    format: string
    type: str

outputs:     # Block outputs
  - name: output1
    format: number
    type: int

build:       # Build configuration
  python-version: "3.10"
  requirements: requirements.txt

gpu: false   # Set to true for GPU blocks
```

</details>

<details markdown="1">
<summary><strong>Makefile</strong> — common commands</summary>

Shortcuts for frequent operations:

```makefile
make setup          # Initialize project
make format         # Format code
```

</details>

<details markdown="1">
<summary><strong>README.md</strong> — block documentation</summary>

User-facing documentation for your block. Provide a complete overview, including:

- What does the block do?
- What are the satellite images used as input?
- What is the resolution of the output images?
- Any specific parameters or configurations that end-users would find useful?

</details>

**Where to start:**

1. **Edit `src/block.py`** — Implement your block logic
2. **Update `clay.yaml`** — Define inputs, outputs, and requirements
3. **Modify `sample_block_inputs.json`** — Add realistic test data
4. **Update `catalog.yaml`** — Document your block for the marketplace

**Files you won't need to modify:**

* `src/entry.py` — Clay's block entry point

<!-- ### Python Environment Setup (Optional but Recommended)

!!! tip "Standard Python Practice - Not Clay-Specific"
    Setting up a Python virtual environment is a general best practice, not specific to Clay. If you're already familiar with Python virtual environments, you can skip this section or use your preferred method.

    **For comprehensive instructions**, see our [Python Setup Guide](python-setup-guide.md).

**Quick Setup:**

=== "venv (Built-in)"

    ```shell
    python3 -m venv venv
    source venv/bin/activate  # Linux/Mac
    ```

=== "conda"

    ```shell
    conda create -n myblock python=3.10
    conda activate myblock
    ``` -->
> **Setup Complete!** Your project is ready for development.

## Build and Test Your Block

Now that your project is set up, let's build and test it locally.

* **Configure Dependencies**

    Update the `build.requirements` field in `clay.yaml` to specify your dependency manager file. By default, it is set to `requirements.txt`. If you use a different file like `conda.yaml`, update `build.requirements` accordingly.

    > **GPU Blocks**
    >
    > If your block uses GPU, update the `gpu` field to `true` in `clay.yaml`. For GPU blocks, it's recommended to use `conda.yaml` for handling dependencies. Clay utilizes conda for blocks with GPU support and ensures NVIDIA drivers are installed to enable GPU execution.

* **Build the Docker Image**

    ```shell
    clay build
    ```
    This will create a Dockerfile if it does not exist and then build an image using the `name` and `version` specified in `clay.yaml`. For example, if the `name` is `myblock` and the `version` is `0.0.1`, a docker image named `myblock:0.0.1` will be created.

     **Available Flags:**

    - `--tag`: Provide the build tag in the format 'repository:tag'. (Default: name:tag, `name` and `tag` mentioned in the clay.yaml config)
    - `--file`: Provide the Dockerfile path. If not provided, Clay will create one using the configuration from clay.yaml.



* **Run Locally**

    ```shell
    clay run  -e INPUT_JSON=\"$(cat <SAMPLE_input_file.json>)\" myblock:0.0.1
    ```

    Expected output:
    ```
    Using configuration located at: /app/specifications/block_specification_dev.yaml
    WARNING - 2024-04-02 09:01:26,122 - job_runner.py:195 - job_block_runner - 'remote-prefix'
    INFO - 2024-04-02 09:01:26,123 - core.py:346 - job_block_runner - Initializing block...
    INFO - 2024-04-02 09:01:26,125 - core.py:348 - job_block_runner - Block initialization complete.
    WARNING - 2024-04-02 09:01:27,130 - core.py:372 - job_block_runner - `CALLBACK_URL` not set
    WARNING - 2024-04-02 09:01:27,133 - block.py:22 - TestBlock - In pre-process
    INFO - 2024-04-02 09:01:27,133 - block.py:25 - TestBlock - Input1 is starting-point
    INFO - 2024-04-02 09:01:27,133 - block.py:31 - TestBlock - In inference
    INFO - 2024-04-02 09:01:27,133 - block.py:36 - TestBlock - In postprocessing
    INFO - 2024-04-02 09:01:27,138 - job_runner.py:470 - job_block_runner - results: [Number(...)]
    ```

    > **Note:** Warnings about `CALLBACK_URL` are expected when running locally. This is only used when blocks are deployed via an orchestrator.



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

    **Available Flags** (all optional — fall back to environment variables or
    values in `clay.yaml` when omitted):

    - `--docker-registry` *(optional)* - Docker image registry to push to (env: `CLAY_DOCKER_REGISTRY`)
    - `--clay-registry` *(optional)* - Clay block registry URL (env: `CLAY_REGISTRY_HOST`)
    - `--documentation-url` *(optional)* - URL for block documentation
    - `--thumbnail-url` *(optional)* - URL for block thumbnail image

    **Example with custom registries:**

    ```shell
    clay publish --clay-registry https://clay.example.com --docker-registry registry.example.com
    ```

* **List Available Blocks**

    ```shell
    clay block list
    ```

    Sample output (the CLI prints one JSON object per block):
    ```json
    [
      {
        "id": "uuid-here",
        "name": "my-block",
        "kind": "block",
        "type": "processing",
        "version": "v1.0.0",
        "docker_image": "registry-url/my-block:v1.0.0",
        "documentation_url": "https://..."
      },
      {
        "id": "another-uuid",
        "name": "another-block",
        "kind": "block",
        "type": "processing",
        "version": "v0.2.0",
        "docker_image": "registry-url/another-block:v0.2.0",
        "documentation_url": "https://..."
      }
    ]
    ```

* **Describe Block Version**

    ```shell
    clay block describe my-block --version v1.0.0
    ```

    Sample output:
    ```json
    {
      "id": "uuid-here",
      "name": "my-block",
      "kind": "block",
      "type": "processing",
      "version": "v1.0.0",
      "docker_image": "registry-url/my-block:v1.0.0",
      "documentation_url": "https://...",
      "thumbnail_url": "https://...",
      "specification": {
        "inputs": [ /* ... */ ],
        "outputs": [ /* ... */ ],
        "parameters": [ /* ... */ ]
      }
    }
    ```

### Deployment to Your Platform

You can deploy your block container to any orchestration platform — publishing
to a registry is optional and only required if you want centralized version
tracking.

Clay blocks are batch workloads (they read inputs, run, and exit), so they map
to job-style primitives rather than long-lived HTTP services:

* **Kubernetes**: Run as Jobs or CronJobs
* **Cloud Services**: AWS ECS, Google Cloud Run, Azure Container Instances
* **Custom Orchestrators**: Integrate with your platform using the Registry API


## Next Steps

Now that you have Clay set up, continue with:

* **[Clay Architecture Overview](overview.md)**: Understand clay architecture
* **[Block Specification](spec.md)**: Understand how to configure your block
* **[Input/Output & Datatypes](IO.md)**: Learn about Clay's type system
* **[Block Development Tutorial](block-development.md)**: Learn how to build your first block