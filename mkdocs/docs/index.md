# Welcome to Clay

[Visit the project on Github](https://github.com/example/clay)

Clay is an open-source framework that helps you package your blocks in a standardized format, enabling seamless deployment across any infrastructure.

## Why Use Clay?
Clay lets you focus on defining your block while abstracting away all the engineering complexity

* **Any ML Framework**: Package blocks built with PyTorch, TensorFlow, scikit-learn, or any framework
* **Geospatial Support**: Built-in handling for raster and vector data types used in satellite imagery
* **Zero Boilerplate**: Auto-generates Dockerfiles, APIs, and container configurations
* **Deploy Anywhere**: Run on Kubernetes, cloud services, or on-premise infrastructure
* **Block Registry**: Version, discover, and manage blocks across your organization
* **Storage Abstraction**: Seamlessly handle S3(currently supported), GCS, Azure, or local file systems

## Who is Clay For?

* **Data Scientists**: Focus on block development without worrying about deployment complexities
* **ML Engineers**: Standardize block deployment across different environments
* **Platform Teams**: Integrate ML blocks into existing infrastructure
* **Organizations**: Enable block discovery, versioning, and orchestration at scale

## How Clay Works

* **Write your block** using any ML framework (PyTorch, TensorFlow, scikit-learn, etc.)
* **Define a specification** in `clay.yaml` with inputs, outputs, and runtime requirements
* **Generate a Dockerfile** using `clay create dockerfile`
* **Build and publish** the container to your registry with `clay publish`
* **Deploy anywhere** — Clay handles the runtime execution and storage abstraction

## Next Steps

Ready to get started? Head to the [Getting Started](getting-started.md) guide to install Clay and create your first block.

### For Pixxel Users

If you're using Clay within the Pixxel platform, see the **[Pixxel Platform Integration](pixxel-integration.md)** guide for organization-specific deployment workflows.