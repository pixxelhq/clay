---
title: Home
order: 1
---

# Welcome to Clay

[Visit the project on Github](https://github.com/pixxelhq/clay)

Clay is an open-source framework that packages your model — called a *block*
in Clay's context — into a standardized format. This enables seamless
deployment across any infrastructure and lets blocks be chained together in a
DAG (Directed Acyclic Graph) effortlessly.

## Why Use Clay?
Clay lets you focus on defining your block while abstracting away all the engineering complexity

* **Any ML Framework**: Package blocks built with PyTorch, TensorFlow, scikit-learn, or any framework
* **Geospatial Support**: Built-in handling for raster and vector data types used in satellite imagery
* **Zero Boilerplate**: Auto-generates Dockerfiles, APIs, and container configurations
* **Deploy Anywhere**: Run on Kubernetes, cloud services, or on-premise infrastructure
* **Block Registry**: Version, discover, and manage blocks across your organization
* **Storage Abstraction**: S3-compatible storage (including MinIO) for cloud artifacts, and the local filesystem for development. Support for GCS and Azure is on the roadmap and not yet available.

## Who is Clay For?

* **Data Scientists**: Focus on model (block) development without worrying about deployment complexities
* **ML Engineers**: Standardize model (block) deployment across different environments
* **Platform Teams**: Integrate ML models/blocks into existing infrastructure
* **Organizations**: Enable model discovery, versioning, and orchestration at scale

## How Clay Works

* **Write your block** using any ML framework (PyTorch, TensorFlow, scikit-learn, etc.)
* **Define a specification** in `clay.yaml` with inputs, outputs, and runtime requirements
* **Build the container image** using `clay build` (a `Dockerfile` is generated automatically when none exists)
* **Publish** the image and registry entry with `clay publish`
* **Deploy anywhere** — Clay handles the runtime execution and storage abstraction

## Next Steps

Ready to get started? Head to the [Getting Started](getting-started.md) guide to install Clay and create your first block.
