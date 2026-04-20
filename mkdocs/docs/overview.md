# Clay Architecture Overview

This document provides a high-level overview of Clay's architecture, components, and how they work together to enable standardized block deployment.

## Glossary

* **Block**: A function that takes inputs, performs computations, and returns outputs. It can be anything from simple arithmetic to complex deep learning blocks. Also Clay's terminology for a packaged block with its specification, container, and metadata.

* **BlockWrapper**: The Python interface that all Clay blocks implement, defining setup, preprocess, inference, and postprocess methods.

* **Orchestrator**: The system responsible for running blocks (e.g., Kubernetes, Docker, cloud services). Pixxel has its own orchestrator called ORCHESTRATOR, which we use to deploy our block on our platform [Platform](https://aurora.pixxel.space/){:target="_blank"}.

* **Runner**: Clay's execution engine that handles block lifecycle, input/output processing, and communication with the orchestrator.

* **Registry**: Centralized service storing block metadata, versions, and specifications.

* **Block Assets**: Files stored in cloud storage (S3) associated with a block, such as pre-trained block weights, configuration files, or reference data. Assets can be shared across all versions or version-specific.

* **Type System**: Clay's standardized data types (Raster, Vector, Number, etc.) that enable blocks to communicate.

## High-Level Workflow

```
┌─────────────────┐
│ Block Developer │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Block Development (Clay)      │
│   • Write BlockWrapper code     │
│   • Define specification        │
│   • Test locally                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Build & Package (Clay CLI)    │
│   • Generate Dockerfile         │
│   • Build container             │
│   • Publish to registry         │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Orchestrator (Your Choice)    │
│   • Pull container              │
│   • Provide environment         │
│   • Execute block               │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Clay Runtime (Runner)         │
│   • Validate inputs             │
│   • Execute BlockWrapper        │
│   • Handle outputs              │
└─────────────────────────────────┘
```

## Key Components

### 1. Clay CLI

Command-line tool for block development:

* Create project scaffolding
* Generate Dockerfiles
* Build containers
* Test locally
* Publish to registry

```bash
clay new ./myblock MyBlock
clay build
clay run  -e INPUT_JSON=\"$(cat <SAMPLE_input_file.json>)\" myblock:0.0.1
```
For complete reference, see [Command Reference](cli-reference.md)

### 2. Clay Python SDK

Runtime library providing:

* **BlockWrapper**: Base class for all blocks
* **Type System**: Raster, Vector, Number, String, Date, Tabular
* **Runners**: Clay's execution engine that handles block lifecycle, input/output processing, and  communication with the orchestrator.
* **Storage**: Abstraction over s3(currently supported), local filesystem
* **Logging**: [Structured JSON logging](logging.md)
* **Progress Tracking**: [Built-in progress reporting](progress.md)

### 3. Block Specification

YAML configuration declaring:

* Block metadata (name, version, author)
* Inputs and outputs with types
* Build instructions (dependencies, Python version)

For complete reference, see [Block Specifications](spec.md).

### 4. Clay Registry

Centralized block management:

* REST API for registry operations
* PostgreSQL backend for metadata
* Version tracking and history
* Block discovery and querying

For complete reference, see [Clay Registry](registry.md).

### 5. Block Assets

Cloud storage for block-related files:

* Upload, download, and list assets via CLI
* Name-level assets shared across all versions
* Version-specific assets for particular releases
* Support for S3 (GCS and Azure coming soon)

For complete reference, see [Block Assets Management](block-assets.md).

### 6. Type System

Standardized data types enabling block interoperability:

| Type | Purpose |
|------|---------|
| **Raster** | GeoTIFF, satellite imagery |
| **Vector** | GeoJSON, polygons |
| **Number** | Integers, floats |
| **String** | Text data |
| **Date** | Temporal data |
| **Tabular** | CSV, structured data |

Types provide validation, metadata, and consistent serialization.

For complete reference, see [Input/Output & Datatypes](IO.md).
## How Blocks Work

### The BlockWrapper Interface

Every Clay block implements four methods:

```python
from clay import BlockWrapper

class MyBlock(BlockWrapper):
    def setup(self, **parameters):
        """Initialize block once at startup"""
        # Load weights, initialize resources
        pass

    async def preprocess(self, **inputs):
        """Prepare inputs for inference"""
        # Validate, transform, prepare data
        return processed_data

    async def inference(self, **processed_data):
        """Run block predictions"""
        # Execute block logic
        return predictions

    async def postprocess(self, **predictions):
        """Format outputs"""
        # Convert to output types
        return formatted_outputs
```

### Execution Flow

1. **Startup**: Runner calls `setup()` with parameters from specification
2. **Input Processing**: Runner validates inputs against specification, downloads files if needed
3. **Preprocessing**: Runner calls `preprocess()` with validated inputs
4. **Inference**: Runner calls `inference()` with preprocessed data
5. **Postprocessing**: Runner calls `postprocess()` with inference results
6. **Output Handling**: Runner validates outputs, uploads files to storage
7. **Completion**: Runner reports success/failure to orchestrator

For tutorial on how to build a block, see [Tutorial](block-development.md)
## Environment Variables

Clay uses environment variables for runtime configuration:

For complete reference, see [Environment Variables](env-requirements.md).


