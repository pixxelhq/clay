# Getting Started

This guide walks you through installing Clay and creating your first block project.

!!! info "What You'll Learn"
    * Installing the Clay CLI
    * Creating a Clay project
    * Building and testing your block locally
    * Publishing to a Registry

## Prerequisite
* **macOS or Linux**: `clay` CLI is supported in macOS and Linux.
* **Docker**: Docker should be [installed](https://docs.docker.com/get-docker/) in your system. It will be used to build image and create container.
* **python**: You should have python >=3.9 installed in your system

## Install clay CLI

* Install Homebrew (Linux users only)

    If you're on Linux/Ubuntu and don't have [Brew](https://brew.sh/), install it by following the instructions [here](https://docs.brew.sh/Homebrew-on-Linux).

    Check installation: `brew --version` should print something like `Homebrew 4.2.12`

* Add Pixxel's Brew Tap
    ```shell
    brew tap example/tap
    ```

* Install Clay
    ```shell
    brew install --formula example/tap/clay
    ```

* Verify Installation

    ```shell
    clay --version
    ```

* Upgrade Clay (for existing installations)

    ```shell
    brew upgrade --formula example/tap/clay
    ```

!!! tip "Troubleshooting"
    If you encounter `command not found: clay`, try running `brew link clay` and then check the Clay version again.

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
│   ├── entry.py                 # Block entry point (don't modify)
│   ├── __version__.py           # Version tracking
├── tests/                      
│   ├── test_block.py           # Local testing script
│   └── sample_block_inputs.json # Example inputs for testing
├── docs/             
│   └── README.md                # Block documentation
├── clay.yaml                    # Clay configuration
├── requirements.txt             # Python dependencies
├── conda.yaml                   # Conda environment (for GPU blocks)
├── Makefile                     # Common commands
├── pyproject.toml              # Python project configuration
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .gitignore                  # Git ignore rules
├── .flake8                     # Linting configuration
└── README.md                    # Project README
```

#### Key Files Explained

=== "block.py"

    **Your block implementation** - This is where you write your actual block logic:

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

=== "clay.yaml"

    **Main configuration file** - Defines your block's metadata and requirements:

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

=== "Makefile"

    **Common commands** - Shortcuts for frequent operations:

    ```makefile
    make setup          # Initialize project
    make format         # Format code
    ```

=== "README.md"

    **Block documentation** - User-facing documentation for your block:

    Provide a complete overview of the block, like:

    - What does the block do?
    - What are the satellite images used as input?
    - What is the resolution of the output images?
    - Are there any specific parameters or configurations that end-users would find useful?

<!-- !!! tip "Where to Start"
    1. **Edit `src/block.py`**: Implement your block logic
    2. **Update `clay.yaml`**: Define inputs, outputs, and requirements
    3. **Modify `sample_block_inputs.json`**: Add realistic test data
    4. **Update `docs/README.md`**: Document your block

!!! info "Files You Won't need to Modify"
    * `src/entry.py` - Clay's block entry point
    * `src/specifications/` - Generated from clay.yaml -->

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
    
## Build and Test Your Block

Now that your project is set up, let's build and test it locally.

* **Configure Dependencies**

    Update the `build.requirements` field in `clay.yaml` to specify your dependency manager file. By default, it is set to `requirements.txt`. If you use a different file like `conda.yaml`, update `build.requirements` accordingly.

    !!! tip "GPU Blocks"
        If your block uses GPU, update the `gpu` field to `true` in `clay.yaml`. For GPU blocks, it's recommended to use `conda.yaml` for handling dependencies. Clay utilizes conda for blocks with GPU support and ensures NVIDIA drivers are installed to enable GPU execution.

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

    !!! note
        Warnings about `CALLBACK_URL` are expected when running locally. This is only used when blocks are deployed on an orchestrator.


✅ **Setup Complete!** Your project is ready for development. 

## Publishing to Registry

Once you've developed and tested your block locally, you can publish different versions of your block
to a registry. With our initiative at Pixxel, we maintain a [clay registry](registry.md) which is a component responsible for storing all blocks along with their different versions. It provides version management, block discovery, and deployment tracking.
Irrespectively, a user is welcome to maintain their own registry for block management using Clay CLI.

### Using Clay CLI

* **Update Version**

    Update the version in `clay.yaml` before publishing:
    ```yaml
    version: v1.0.0  # Follow semantic versioning
    ```

* **Publish to Registry**

    ```shell
    clay publish
    ```

    **Available Flags:**

    - `--docker-registry` - Docker image registry to push to (env: `CLAY_DOCKER_REGISTRY`)
    - `--clay-registry` - Clay block registry URL (env: `CLAY_REGISTRY_HOST`)
    - `--documentation-url` - URL for block documentation
    - `--thumbnail-url` - URL for block thumbnail image

    **Example with custom registries:**

    ```shell
    clay publish --clay-registry https://clay.example.com --docker-registry registry.example.com
    ```

* **List Available Blocks**

    ```shell
    clay block list
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
      "documentation_url": "https://..."
    }
    ```

* **Describe Block Version**

    ```shell
    clay block describe my-block --version v1.0.0
    ```

### Deployment to Your Platform

Once published to the registry, you can deploy your block to your orchestration platform:

* **Kubernetes**: Deploy as Jobs, Deployments, or CronJobs
* **Cloud Services**: AWS ECS, Google Cloud Run, Azure Container Instances
* **Custom Orchestrators**: Integrate with your platform using the Registry API


## Next Steps

Now that you have Clay set up, continue with:

* **[Clay Architecture Overview](overview.md)**: Understand clay architecture
* **[Block Specification](spec.md)**: Understand how to configure your block
* **[Input/Output & Datatypes](IO.md)**: Learn about Clay's type system
* **[Block Development Tutorial](block-development.md)**: Learn how to build your first block