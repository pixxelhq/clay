# Changelog

All notable changes to the Clay SDK and CLI are recorded here. Both artifacts ship under a single version — each entry covers changes across both.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/). Versions follow [PEP 440](https://peps.python.org/pep-0440/) so the same string works for PyPI and for GitHub tags (`v1.9.0`, `v1.9.0rc1`).

## Unreleased
### Features
- `clay dockerfile` prints the Dockerfile that `clay build` generates from
  `clay.yaml`. To customize it, run `clay dockerfile > Dockerfile` and build
  with `clay build -f Dockerfile`.
- `clay publish` accepts `-f, --file` to build with your own Dockerfile, like
  `clay build`.
- `clay build` and `clay publish` print the image tag before the build starts.
- `clay build --help` and `clay publish --help` say that `build` only makes a
  local image and `publish` also pushes it and registers the block.
- `cuda: true` in `clay.yaml` selects the CUDA base image. The conda
  environment is created with `python=<python-version>` (default `"3.10"`),
  and with `gdal` if `gdal: true`. A Python version in the conda file must
  match `python-version`. Packages in `apt-get` are now installed in the CUDA
  image too; previously they were ignored.

### Deprecations
- `conda: true` in `clay.yaml` is an alias for `cuda: true` and prints a
  warning. It will be removed in the next minor release.

### Bug Fixes
- `clay build` supports `python-version` `"3.10"`, `"3.11"` and `"3.12"`, and
  packages and the entrypoint use that Python. Previously the image was
  Ubuntu 22.04: `"3.12"` failed, and `"3.11"` installed packages for Python
  3.10. Other versions now stop with an error before the build starts. If
  `python-version` is not set, Clay uses `"3.10"`.
- The base image follows `clay.yaml`. With `gdal: false` it is the official
  `python:<version>-slim` image. With `gdal: true` it is the OSGeo GDAL image,
  which has GDAL and its Python bindings (`osgeo`): GDAL 3.8.5 for `"3.10"`
  and GDAL 3.12.4 for `"3.12"`. There is no OSGeo image with Python 3.11, so
  `gdal: true` with `"3.11"` prints a warning and uses the
  `python:3.11-slim` image without GDAL. Previously `gdal` was
  ignored and every image used GDAL 3.6.3. Blocks that import `osgeo` must
  now set `gdal: true`. The `rasterio` and `fiona` wheels include their own
  GDAL; on a `python:<version>-slim` image they need `libexpat1` in
  `apt-get`. In the OSGeo images, `osgeo.gdal_array` (`ReadAsArray`,
  `WriteArray`) needs `numpy<2` in `requirements`.
- The `python:*-slim` and OSGeo images have no C compiler. If a package in
  `requirements` must be compiled, add `build-essential` to `apt-get`.
- The block runs as a non-root user (UID `10001`, or `mambauser` with
  `cuda: true`). It can write to `/tmp` and its home directory, but not to
  `/app`.
- The image sets `PYTHONUNBUFFERED=1`, so log lines appear immediately.
  Previously it set the misspelled `PYTHONBUFFERED`.
- All base images and the `uv` image have pinned versions.
- `apt-get` packages are installed without recommended packages, and the apt
  package lists are removed in the same layer.
- `clay run` with `gpu: true` uses only `--gpus all`. Previously it also passed
  `--runtime nvidia`, which fails on hosts that have only the current NVIDIA
  Container Toolkit.
- `clay build` and `clay publish` generate the Dockerfile from `clay.yaml` on
  each build, in a temporary folder. Previously the first build wrote a
  `Dockerfile` into the project and later builds reused it, so changes to
  `build:` (for example the Python version or `apt-get` packages) did not
  reach the image. A `Dockerfile`
  left in the project by an older Clay version is ignored with a warning; pass
  `-f Dockerfile` to build with it.
- `clay build` writes values from `clay.yaml` into the Dockerfile as they are.
  Previously characters such as `+` and `&` were HTML-escaped, so
  `apt-get: [g++]` gave `g&#43;&#43;` and the build failed.
- `clay new` no longer deletes an existing project directory. If the directory
  exists and is not empty, it stops with an error and a hint about the new
  `--force` flag. `--force` writes the template over the directory and keeps
  files that are not part of the template.
- `clay new` now writes the project to the requested directory when its path
  contains `src` (for example `~/src/projects`). Only the template's own `src/`
  folder is renamed to the block name; the output path is no longer searched.
  Previously it failed.
- `clay build` no longer runs `sudo docker build`. It runs `docker` as the
  current user, like `clay push` and `clay run`, so it works in CI and other
  non-interactive shells and no longer leaves root-owned files in `~/.docker`.
- `clay build`, `clay publish`, `clay push` and `clay run` check that the
  Docker daemon is reachable first. If it is not, they show Docker's error and
  a hint (install Docker, start it, or on Linux join the `docker` group)
  instead of `exit status 1`.
- The Clay registry no longer logs the database connection string, which
  included the user name and password, when it cannot reach Postgres on
  startup. The error now shows only the database name and host. A missing or
  wrong `DB_MIGRATION_PATH` is reported as a migrations error instead.
- `clay new` accepts block names with `-`, `_` and digits, so the
  `clay new --help` example runs. Names are derived from the given name:
  `my-block`, `my_block` and `MyBlock` all give `my-block` for the `clay.yaml`
  name, the image and the project folder, `my_block` for the Python package,
  and `MyBlock` for the class.
  The generated `tests/test_block.py` now imports the right module; it failed
  with `ModuleNotFoundError` for names such as `MyBlock`.
- `clay build` no longer depends on the name of the project folder. When it
  generates a Dockerfile, it uses the folder that holds `entry.py`, named after
  the `clay.yaml` name or, for older projects, after the project folder. A
  project cloned into a folder with another name builds. If neither folder
  exists, it stops with a clear error before Docker runs.
- `clay publish` checks the Clay registry before it builds and pushes. If the
  version in `clay.yaml` is already published, it stops with an error and a
  hint to bump `version`, instead of overwriting the published image tag and
  then being rejected by the registry.

## v1.3.0 - 2026-10-01
### New Features
- `DateValidation` is no longer an empty placeholder: it carries `min_date`,
  `max_date`, and `date_format` (`date_only` or `date_time`), so blocks can bound
  date inputs the way number and string inputs already are. Enforced by the Go
  validator (`ValidateDate`) and the Python `validate_input` datatypes helper.
  Design and rationale: pixxelhq/clay#11.
- `pixxel-datatypes` bumped to 1.1.0 with the regenerated bindings.

## v1.1.0 - 2026-08-18
### New Features
- `INPUT_JSON_URI` lets the runner fetch its input JSON from remote storage
  instead of reading it inline from `INPUT_JSON`. The URI is resolved through the
  clay storage provider abstraction, so any supported backend works and the
  scheme selects the provider. When `INPUT_JSON_URI` is unset, the existing
  `INPUT_JSON` behaviour is unchanged.

## v1.0.0 - 2026-07-22
### New Features
- Clay is now released as open source under the Apache License 2.0.
- Added `LICENSE`, `SECURITY.md`, and GitHub issue / pull-request templates.
- Rewrote top-level `README.md`, `CONTRIBUTING.md`, and `mkdocs` documentation
  for external users; removed internal deployment guide.
- Cleaned `setup.py` package metadata (license, description) and dropped stale
  Python 3.8 / 3.9 classifiers.
### Fixes
- Removed dead `clay-docs.Dockerfile` and unused `build-docs-docker-image`
  Makefile target.
- Removed internal contact metadata from the Clay Registry Swagger
  specification.

## v1.3.1a2 - 2025-05-02
### New Features
- Introduced `stac_url` in `Raster` datatype.
- Added `add_asset` function to upload an input/output asset explicitly from a block.
- Added `set_disclaimer` function to send block disclaimers.
- Removed Orchestrator-related references from Clay.
- Released clay python SDK version 1.3.1a2.
### Fixes
- Correct sorting when listing blocks.
- Removed environment-specific flag from clay CLI.

## v0.6.1 - 2025-02-05
### New Features
- Deprecation notice for `Types` in Clay.
### Fixes
- Return `kind` and `type` in all `get block` APIs.
- Updated Clay registry host in GitHub publish pipeline.

## v0.6.0 - 2024-09-18
### New Features
- Input assets are now pushed to S3 for `job_runner_v2`.
### Fixes
- Minor refactor of `job_runner_v2`.

## v0.5.0 - 2024-09-11
### New Features
- Added `group` support to data spec — @pranjaldatta. [043af0d](https://github.com/pixxelhq/clay/commit/043af0d7b7d2ef6067fa0fbbe7effb4c7a6b7016)
### Fixes
- Input vector files now get uploaded to S3 for both inferences and workflows — @sanafirdaus. [eb435f0](https://github.com/pixxelhq/clay/commit/eb435f0082ae8be1e261b5b1c743484f082f2b3f)

## v0.4.11 - 2024-08-14
### New Features
- Orchestrator callback URL is now configurable and injected at runtime — @pranjaldatta. [4107ed6](https://github.com/pixxelhq/clay/commit/4107ed6e546772a5bf14ecabe8b04bbb70d994e5)

## v0.4.10 - 2024-07-23
### New Features
- Support for stac URLs in `RasterProperties` — @pranjaldatta. [4f0031e](https://github.com/pixxelhq/clay/commit/4f0031e229c5d516a9e79c080eac6a13b9862761)

## v0.4.6 - 2024-06-28
### New Features
- Added `date` to `RasterProperties` — @sanafirdaus. [6e50abd](https://github.com/pixxelhq/clay/commit/6e50abd875d95b5e886af307a1e8f26cd44ec078)
- Added time metrics to inference callback — @pranjaldatta. [c3c192b](https://github.com/pixxelhq/clay/commit/c3c192b16f3863453c0580bf8b83c767143f97b0)
### Fixes
- Improved time calculation for total block runtime and inference runtime — @pranjaldatta. [d2c7510](https://github.com/pixxelhq/clay/commit/d2c751086cc6fe8deea73f266804a315bf3ed9f0)
