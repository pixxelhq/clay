# CLI Reference

The Clay CLI provides commands for creating, building, publishing, and managing ML model blocks.

## General Commands

### Version

Display the current version of the Clay CLI.

```shell
clay version
```

### Help

Get help for any command.

```shell
clay <command> --help
```

---

## Model Commands

Commands for creating, building, and running models.

### Create Project

Generate starter files for a new model project.

```shell
clay create project <outputDir> <modelName>
```

| Argument | Description |
|----------|-------------|
| `outputDir` | Directory where project files will be created |
| `modelName` | Name of the model |

### Build

Build a Docker image from `clay.yaml`.

```shell
clay build [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-t, --tag` | Build tag (format: `repository:tag`) | — |
| `-f, --file` | Dockerfile path | — |
| `--no-cache` | Disable Docker layer caching | `false` |
| `--secret` | Secret to expose to build | — |
| `--build-arg` | Build-time variables | — |
| `--platform` | Target platform for build | — |

### Push

Push a Docker image to the registry.

```shell
clay push [IMAGE]
```

| Argument | Description |
|----------|-------------|
| `IMAGE` | Docker image to push |

### Run

Run the Docker image locally.

```shell
clay run [IMAGE NAME] [ARG...] [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-e, --env` | Set environment variables (`KEY=VALUE` format) | — |
| `-f, --file` | Path to file containing input data | — |

### Publish

Build, push image, and publish to Clay registry in one command.

```shell
clay publish [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--docker-registry-host` | Docker registry URL | `REDACTED.dkr.ecr.us-east-2.amazonaws.com` |
| `--model-registry-host` | Clay registry host | `http://localhost:8080` |
| `--documentation-url` | Model documentation URL | — |
| `--thumbnail-url` | Model thumbnail URL | — |

---

## Block Commands

Commands for managing blocks in the registry.

### List Blocks

List available blocks in the registry.

```shell
clay block list [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-n, --name` | Filter by block name | — |
| `-v, --version` | Specific version to list | — |
| `--host` | Clay registry host | `https://clay-registry.example.com` |

### Describe Block

List all versions of a block or get details for a specific version.

```shell
clay block describe <name> [flags]
```

| Argument | Description |
|----------|-------------|
| `name` | Name of the block |

| Flag | Description | Default |
|------|-------------|---------|
| `-v, --version` | Specific version to describe | — |
| `--host` | Clay registry host | `https://clay-registry.example.com` |

---

## Block Assets Commands

Commands for managing block assets in cloud storage.

### Upload Assets

Upload files or directories to cloud storage for a block. Assets can be stored at the block name level (shared across versions) or version-specific.

```shell
clay block assets upload <path> [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-n, --name` | Name of the block (required) | — |
| `-v, --version` | Version of the block (optional) | — |
| `--bucket` | Storage bucket name (required) | — |
| `--provider` | Storage provider: `s3`, `gcs`, `azure` | `s3` |
| `--region` | Storage region (required for S3) | — |
| `--readme` | Process markdown templates before upload | `false` |

### List Assets

List all assets stored in cloud storage for a block.

```shell
clay block assets list [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-n, --name` | Name of the block (required) | — |
| `-v, --version` | Version of the block (optional) | — |
| `--bucket` | Storage bucket name (required) | — |
| `--provider` | Storage provider: `s3`, `gcs`, `azure` | `s3` |
| `--region` | Storage region (required for S3) | — |

### Download Assets

Download an asset file from cloud storage. If a version is specified, it checks version-specific assets first, then falls back to name-level assets.

```shell
clay block assets download <asset-path> [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-n, --name` | Name of the block (required) | — |
| `-v, --version` | Version of the block (optional) | — |
| `-o, --output` | Local path to save the downloaded asset | `.` |
| `--bucket` | Storage bucket name (required) | — |
| `--provider` | Storage provider: `s3`, `gcs`, `azure` | `s3` |
| `--region` | Storage region (required for S3) | — |

---

## Upload Commands

Commands for uploading model assets.

### Upload Readme

Upload the README documentation for a block to cloud storage for the marketplace catalog.

```shell
clay upload readme [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-n, --name` | Name of the block | — |
| `-v, --version` | Version of the block | — |
