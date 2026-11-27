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

### Errors

When a command fails, Clay prints one `error:` line that says what failed and, when it can tell what might be wrong, a `hint:` line with what to do next:

```console
error: clay.yaml: build.python-version must be text, not a number
hint: put the value in quotes so that YAML reads it as text
```

`clay build`, `clay push`, `clay publish` and `clay run` show the full output of Docker as it runs. If Docker fails, Clay names the command and its exit code, and the cause is in the Docker output above:

```console
error: docker build failed (exit 1)
hint: the docker build output above shows the cause
```

---

## Project Commands

Commands for creating, building, and running blocks.

### New

Scaffold a new block project in the directory `<path>`. `<path>` must not exist or must be empty; to make a directory that already holds files a block project, use [`clay init`](#init).

```shell
clay new <path> [flags]
```

| Argument | Description |
|----------|-------------|
| `path` | Project directory. Its last part is the block name, unless `--name` is given |

| Flag | Description | Default |
|------|-------------|---------|
| `--name` | Block name: letters, digits, `-` and `_` | last part of `path` |
| `--with` | Add optional files: `catalog`, `conda`, `pre-commit`. Repeat the flag or separate values with commas | — |

For example, `clay new my-block` creates `./my-block`, and `clay new .` makes the current directory a project when it is empty. Use `--name` when the directory name is not a valid block name, or to keep capitals that the folder name loses: `clay new resnet.v2 --name resnet-v2`. The older form `clay new <path> <name>` still works: it creates `<path>/<name in kebab-case>` and prints a deprecation warning. It will be removed in a future release.

If the project directory already exists and holds files, `clay new` stops with an error and changes nothing. The error suggests `clay init`. `clay new` never overwrites or deletes anything.

The project contains only the files every block needs: `clay.yaml`, `requirements.txt`, `requirements-dev.txt`, the block package, `tests/`, `README.md`, `pyproject.toml`, `.gitignore` and `.dockerignore`. `clay new` does not run `git init`, install git hooks or download tools. Use `--with` to add more files:

| Option | Adds |
|--------|------|
| `catalog` | `catalog.yaml`, to describe the block in a catalog (see [Block Assets](block-assets.md)) |
| `conda` | `conda.yaml`, and sets `build.conda: true` and `build.requirements: conda.yaml` in `clay.yaml` |
| `pre-commit` | `.pre-commit-config.yaml` with ruff hooks, and `pre-commit` in `requirements-dev.txt`. Run `pre-commit install` to install the hooks |

For example, `clay new my-block --with catalog,conda`.

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

Make the current directory a block project. The directory may already hold files, such as a repository with your model code. The block name is the name of the current directory, unless `--name` is given.

```shell
clay init [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--name` | Block name: letters, digits, `-` and `_` | name of the current directory |
| `--with` | Add optional files: `catalog`, `conda`, `pre-commit`, as with `clay new` | — |
| `-f, --force` | Overwrite existing files with the template | `false` |

`clay init` keeps files that already exist. A file with the same name as a template file, such as `README.md` or `requirements.txt`, is not changed, and `clay init` prints `Skipped:` for it so you can merge it by hand.

If the directory already has a `clay.yaml`, `clay init` stops with an error and changes nothing. With `--force`, it writes the template anyway and overwrites files with the same name as a template file. Other files, such as model weights, are always kept, and `clay init` never deletes anything.

`clay init` refuses to run in the filesystem root, in your home directory, and in the `Desktop`, `Documents` and `Downloads` folders directly in it, even with `--force`. Create a folder for the project instead, for example with `clay new my-block`. Folders inside them, such as `~/Documents/my-model`, work as usual.

The block name follows the same rules as in [`clay new`](#new).

### Build

Build a Docker image locally from `clay.yaml`. The image stays on this machine; to push it and register the block, use [`clay publish`](#publish). Clay generates the Dockerfile from `clay.yaml` on each build, so a change to `build:` changes the next image. The generated file is not written into the project.

```shell
clay build [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-t, --tag` | Build tag (format: `repository:tag`) | `<name>:<version>` from `clay.yaml` |
| `-f, --file` | Dockerfile path. Use your own Dockerfile instead of the generated one | — |
| `--no-cache` | Disable Docker layer caching | `false` |
| `--secret` | Secret to expose to build | — |
| `--build-arg` | Build-time variables | — |
| `--platform` | Target platform for build | — |

If `-f` is not given and the project has a `Dockerfile` (for example from an older Clay version), `clay build` and `clay publish` build with it. Changes to `build:` in `clay.yaml` do not apply to it; delete it to use the generated one.

The base image depends on `build.python-version`, `build.gdal` and `build.conda`; see [Base image](spec.md#base-image). Clay stops with an error if `python-version` is not `"3.10"`, `"3.11"` or `"3.12"`, or if `gdal: true` is used with Python `"3.11"` without `conda: true` (there is no OSGeo GDAL image for it; the error lists the fixes).

### Dockerfile

Print the Dockerfile that `clay build` generates from `clay.yaml`.

```shell
clay dockerfile
```

To customize the Dockerfile, save it and build with `-f`:

```shell
clay dockerfile > Dockerfile
clay build -f Dockerfile
```

### Push

Push a block's Docker image to a Docker registry.

```shell
clay push [IMAGE] [flags]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `IMAGE` | Docker image to push, with its registry, for example `registry.example.com/my-block:v0.0.1` | — |

| Flag | Description | Default |
|------|-------------|---------|
| `--docker-registry` | Registry to push `<name>:<version>` to. Used only without `IMAGE` | `CLAY_DOCKER_REGISTRY` |

Without `IMAGE`, run it in the project folder. `clay push` tags `<name>:<version>` from `clay.yaml`, the image that `clay build` makes, as `<registry>/<name>:<version>` and pushes it. The registry comes from `--docker-registry` or `CLAY_DOCKER_REGISTRY`, as in [`clay publish`](#publish):

```shell
clay push --docker-registry registry.example.com
```

With `IMAGE`, `clay push` pushes that image as it is named, and does not need `clay.yaml`. The name must include a registry or a Docker Hub account, for example `registry.example.com/my-block:v0.0.1` or `my-account/my-block:v0.0.1`. A name without `/`, such as `my-block:v0.0.1`, is rejected, because Docker would push it to `docker.io/library`, where only official images can be pushed.

### Run

Run a block's Docker image locally. Run it in the project folder: it reads `gpu` from `clay.yaml`.

```shell
clay run [IMAGE] [ARGS...] [flags]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `IMAGE` | Docker image to run | `<name>:<version>` from `clay.yaml`, the image that `clay build` makes |
| `ARGS` | Arguments passed to the container. They need `IMAGE` before them, or the first one is taken as the image | — |

| Flag | Description | Default |
|------|-------------|---------|
| `-e, --env` | Set environment variables (`KEY=VALUE` format) | — |
| `--input` | JSON input array to pass to the block | — |
| `--input-uri` | URI of the input JSON, for example `s3://bucket/path/input.json` | — |

For example, `clay run --input "$(cat tests/sample_block_inputs.json)"` runs the image that `clay build` made. See [Passing input](env-requirements.md#2-passing-input-input-and-input-uri).

If `gpu: true` is set in `clay.yaml`, the container runs with `--gpus all`. This needs the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

### Publish

Build the image, push it to a Docker registry, and register the block in the Clay registry in one command. The image is tagged `<docker-registry>/<name>:<version>`. Of the build flags, only `-f, --file` is accepted; use `clay build` for `--no-cache`, `--secret`, `--build-arg` and `--platform`.

```shell
clay publish [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--docker-registry` | Docker image registry. Required unless `CLAY_DOCKER_REGISTRY` is set | — |
| `--clay-registry` | Clay block registry URL. Required unless `CLAY_REGISTRY_HOST` is set | — |
| `-f, --file` | Dockerfile path. Use your own Dockerfile instead of the generated one | — |
| `--catalog-url` | URL of the published `catalog.yaml` (see [Upload Catalog Media](#upload-catalog-media)) | — |

Before building, `clay publish` asks the Clay registry whether the `name` and `version` from `clay.yaml` are already published. If they are, it stops with an error before building or pushing anything. Bump `version` in `clay.yaml` to publish a new version.

The check sends `version` exactly as written in `clay.yaml`, but the registry stores each version in full `MAJOR.MINOR.PATCH` form, without a leading `v`: `v0.0.1` is stored as `0.0.1`, and `0.1` as `0.1.0`. So:

- With all three parts and no `v`, such as `0.0.1`, the check works: a published version is found before anything is built. A `clay.yaml` with `apiVersion: clay/v1`, which is what `clay new` and `clay init` write, only accepts this form.
- With a `v`-prefixed version such as `v0.0.1`, or a short version such as `0.1`, both possible only without `apiVersion: clay/v1`, the check does not find it. `clay publish` then builds the image and pushes it under the same tag as the published image, and only after that does the registry reject the version as already published.

The registry also rejects a `version` that is not a semantic version, after the image has been pushed.

---

## Block Commands

Commands for managing blocks in the registry.

### List Blocks

List blocks in the registry, as JSON.

```shell
clay block list [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-n, --name` | List all versions of this block | — |
| `-v, --version` | With `--name`, show only this version | — |
| `--clay-registry` | Clay block registry URL (required) | — |

Without flags, `clay block list` shows the latest version of each block: the highest semantic version. `-v` is ignored without `-n`. Pass the version as the registry stores it, without a leading `v` (see [Publish](#publish)); `-v latest` shows the highest version.

`clay block list` and `clay block describe` do not read `CLAY_REGISTRY_HOST`: pass `--clay-registry`. Only `clay publish` reads the variable.

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
| `--clay-registry` | Clay block registry URL (required) | — |

As with `clay block list`, pass the version without a leading `v`, for example `-v 0.0.1` for `version: v0.0.1` in an older `clay.yaml`. `-v latest` describes the highest version.

---

## Block Assets Commands

Commands for managing block assets in cloud storage. The remote location is specified with a single `--url` flag.

Supported URL form (AWS S3 virtual-hosted HTTPS):

- `https://<bucket>.s3.<region>.amazonaws.com/<prefix>/`

The region must be in the URL. `s3://` URIs, other hosts (including path-style `https://s3.<region>.amazonaws.com/<bucket>/` URLs and hosts without a region), and URLs with a query string or fragment are rejected. See [Block Assets](block-assets.md).

### Upload Assets

Upload a file or directory to cloud storage at the location given by `--url`. A file is uploaded to `<--url>/<filename>`. For a directory, its contents are uploaded under `--url` with their paths relative to the directory; the directory's own name is not added.

```shell
clay block assets upload <path> [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Complete storage URL where assets will be uploaded (required) | — |

### Upload Catalog Media

Publish the media declared in the `catalog.yaml` in the current working directory. Each file in its `media:` section is uploaded to `<--url>/<key>/<filename>`; the local folders are dropped. Then a copy of `catalog.yaml`, with each `media:` value set to its uploaded URL, is uploaded next to the media, and its URL is printed for `clay publish --catalog-url`. Your `catalog.yaml` is not changed. `media:` values that are already `http(s)` URLs are not uploaded again. Bake the block/version into `--url`.

Each local `media:` path must name an existing file inside the current directory, relative to it. Absolute paths, paths that leave the directory with `..`, symlinks that point outside it, and directories are rejected. The `catalog.yaml` that `clay new --with catalog` creates lists `thumbnail.png`, `sample_input.png` and `sample_output.png`, which it does not create; add them or change the paths first.

```shell
clay block assets upload-catalog [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Complete storage URL where the catalog media will be uploaded (required) | — |

### List Assets

List the assets whose keys start with the path in `--url`. End `--url` with `/` to list one folder: `.../my-block/v1` also matches `.../my-block/v10/`. The list is printed to standard error.

```shell
clay block assets list [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Complete storage URL to list (required) | — |

### Download Assets

Download the asset at `--url` to the local filesystem. `--url` must point at a single file. If `--output` is an existing directory, the file is saved in it under its remote name; otherwise `--output` is the file path, and missing parent directories are created. An existing file at that path is overwritten.

```shell
clay block assets download [flags]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Complete storage URL of the asset to download (required) | — |
| `-o, --output` | Local path to save the downloaded asset (directory or filename) | `.` |
