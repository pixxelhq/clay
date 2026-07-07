---
title: CLI Reference
order: 11
---

# CLI Reference

The Clay CLI provides commands for creating, building, publishing, and managing ML blocks.

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

## Project Commands

Commands for creating, building, and running blocks.

### New

Scaffold a new block project at the given path.

```shell
clay new <path> <name>
```

| Argument | Description |
|----------|-------------|
| `path` | Directory where project files will be created |
| `name` | Name of the block |

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

### Publish

Build, push image, and publish to Clay registry in one command.

```shell
clay publish [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--docker-registry` | Docker image registry (env: `CLAY_DOCKER_REGISTRY`) | — |
| `--clay-registry` | Clay block registry URL (env: `CLAY_REGISTRY_HOST`) | — |
| `--documentation-url` | Block documentation URL | — |
| `--thumbnail-url` | Block thumbnail URL | — |

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
| `--clay-registry` | Clay block registry URL (env: `CLAY_REGISTRY_HOST`) | — |

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
| `--clay-registry` | Clay block registry URL (env: `CLAY_REGISTRY_HOST`) | — |

---

## Block Assets Commands

Commands for managing block assets in cloud storage. The remote location is specified with a single `--url` flag.

Supported URL form (AWS S3 virtual-hosted HTTPS):

- `https://<bucket>.s3.<region>.amazonaws.com/<prefix>/`

The region must be in the URL. `s3://` URIs and other hosts are rejected.

### Upload Assets

Upload a file or directory to cloud storage at the location given by `--url`.

```shell
clay block assets upload <path> [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Complete storage URL where assets will be uploaded (required) | — |
| `--catalog` | Name of a `catalog.yaml` inside `<path>` (the model repo directory). Uploads each file declared in its `media:` section to `<--url>/<relative-path>` and rewrites those `media:` values to the uploaded URLs. Bake the block/version into `--url`. | — |
| `--out` | Where to write the rewritten catalog (with `--catalog`); relative paths resolve against `<path>`. Defaults to overwriting the `--catalog` file in place. | — |

### List Assets

List all assets at the location given by `--url`.

```shell
clay block assets list [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Complete storage URL to list (required) | — |

### Download Assets

Download the asset at `--url` to the local filesystem. `--url` must point at a single file.

```shell
clay block assets download [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Complete storage URL of the asset to download (required) | — |
| `-o, --output` | Local path to save the downloaded asset (directory or filename) | `.` |
