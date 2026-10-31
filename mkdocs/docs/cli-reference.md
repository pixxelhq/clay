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

Scaffold a new block project in the directory `<path>`.

```shell
clay new <path> [flags]
```

| Argument | Description |
|----------|-------------|
| `path` | Project directory. Its last part is the block name: letters, digits, `-` and `_` |

| Flag | Description | Default |
|------|-------------|---------|
| `-f, --force` | Write the template into an existing non-empty project directory | `false` |

For example, `clay new my-block` creates `./my-block`, and `clay new .` makes the current directory a project. The older form `clay new <path> <name>` still works: it creates `<path>/<name in kebab-case>` and prints a deprecation warning. It will be removed in a future release.

If the project directory already exists and is not empty, `clay new` stops with an error and changes nothing. With `--force`, the template files are written into it: files with the same name as a template file are overwritten, and all other files are kept. `clay new` never deletes a directory.

Clay derives every name from the block name. A name starts with a letter, ends with a letter or digit, and contains letters, digits, `-` and `_`.

Words are separated by `-`, `_` or a capital letter, so `my-block`, `my_block` and `MyBlock` all give the same names:

| Used for | Rule | Result |
|----------|------|--------|
| `clay.yaml` name and image | words joined with `-`, lower case | `my-block` |
| Python package folder | words joined with `_`, lower case | `my_block` |
| Python class | each word starts with a capital | `MyBlock` |

A name with no separator or capital, such as `myblock`, is one word.

`clay build` finds the package folder from the `clay.yaml` name, so the project folder can have any name. If you change `name` after the project is created, keep the project folder name equal to the package folder name, or rename the package folder to match.

### Init

Scaffold a new block project in the current directory. The block name is the name of the current directory.

```shell
clay init [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-f, --force` | Write the template into the current directory when it is not empty | `false` |

`clay init` follows the same rules as `clay new`: it stops with an error if the directory is not empty, unless you pass `--force`.

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

### Upload Catalog Media

Publish the media declared in the `catalog.yaml` in the current working directory. Each file in its `media:` section is uploaded to `<--url>/<relative-path>` and its value is rewritten to the uploaded URL, in place; the rewritten `catalog.yaml` is then uploaded alongside its media. Already-uploaded URLs are skipped, so re-running is idempotent. Bake the block/version into `--url`.

```shell
clay block assets upload-catalog [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Complete storage URL where the catalog media will be uploaded (required) | — |

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
