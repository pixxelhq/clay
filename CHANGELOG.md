# Changelog

All notable changes to the Clay SDK and CLI are recorded here. Both artifacts ship under a single version — each entry covers changes across both.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/). Versions follow [PEP 440](https://peps.python.org/pep-0440/) so the same string works for PyPI and for GitHub tags (`v1.9.0`, `v1.9.0rc1`).

## Unreleased
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
