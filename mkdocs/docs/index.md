---
title: Home
order: 1
---

# Welcome to Clay

[Visit the project on Github](https://github.com/pixxelhq/clay)

Clay is an open-source framework that packages your model — called a *block*
in Clay's context — into a standardized format: a Docker image with typed
inputs and outputs. Any container platform can run the image, and an external
orchestrator can chain blocks together.

## Why Use Clay?
Clay lets you focus on defining your block while abstracting away all the engineering complexity

* **Any ML Framework**: Package blocks built with PyTorch, TensorFlow, scikit-learn, or any framework
* **Geospatial Support**: Built-in handling for raster and vector data types used in satellite imagery
* **Less Boilerplate**: Generates the `Dockerfile` from `clay.yaml` and builds the image. The block runs as a one-shot job; an HTTP serve mode is planned
* **Run Anywhere**: Clay builds and pushes standard Docker images, so any container platform can run them, such as Kubernetes, cloud container services, or your own servers
* **Block Registry**: Version, discover, and manage blocks across your organization
* **Storage Abstraction**: AWS S3 for cloud artifacts (MinIO and other S3-compatible stores through `AWS_ENDPOINT_URL`), and the local filesystem for development. Support for GCS and Azure is on the roadmap and not yet available.

## Who is Clay For?

* **Data Scientists**: Focus on model (block) development without worrying about deployment complexities
* **ML Engineers**: Standardize model (block) deployment across different environments
* **Platform Teams**: Integrate ML models/blocks into existing infrastructure
* **Organizations**: Enable model discovery and versioning through the block registry

## How Clay Works

* **Write your block** using any ML framework (PyTorch, TensorFlow, scikit-learn, etc.)
* **Define a specification** in `clay.yaml` with inputs, outputs, and runtime requirements
* **Build the container image** using `clay build` (the `Dockerfile` is generated from `clay.yaml` on each build)
* **Publish** the image and registry entry with `clay publish`
* **Run the image** on any container platform — the Clay runtime inside it handles execution and storage

## Next Steps

Ready to get started? Head to the [Getting Started](getting-started.md) guide to install Clay and create your first block.
