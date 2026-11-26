# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Clay is an open-source framework for packaging ML models as deployable blocks. It consists of:
- **Clay CLI** (Go): Command-line tool for creating projects, building containers, and managing model registry
- **Clay Python package**: Runtime library used by packaged models for execution

## Project Structure

The repository is organized as follows:

- `cmd/` - Go CLI commands (new, init, build, run, push, publish, block, etc.)
- `pkg/` - Go packages for config, docker, registry client, storage, catalog, block names, logging
- `python/clay/` - Python runtime library
  - `runners/` - Job runner that drives the block lifecycle
  - `storage/` - File system abstractions (S3, local)
  - `callback/` - Progress reporting mechanisms
- `api/bootstrap/` - Project templates for `clay new` and `clay init`
- `registry/` - Model registry service with PostgreSQL backend
- `examples/` - Sample models and Docker Compose setups
- `mkdocs/` - Documentation site

## Development Commands

### Testing
- `make test` - Go tests of the root module (`go test ./...`) and Python tests; does not run the `registry/` module's tests
- `make test-go` - Go tests of the root module, except packages whose path contains `registry` (that is, `pkg/registry`, the CLI's registry client)
- `make test-python` - Python tests only (`python/` and `proto/python/`)
- `make test-registry` - Registry service tests (`registry/` is a separate Go module)

### Code Quality
- `make format` - Format Python code with ruff and run pre-commit hooks
- `make pre-commit` - Run pre-commit hooks manually

### Building
- `make package` - Build Python package distribution
- `make go-binaries` - Build cross-platform CLI binaries

### Documentation
- `make build-docs` - Build MkDocs documentation
- `make serve-docs` - Serve docs locally on http://localhost:8000
- `make spell-check-docs` - Check documentation spelling

### Docker Testing
- `make test-integration` - Docker integration tests for `pkg/docker` (needs a running Docker daemon)

## Architecture

### Block Execution Flow
1. Blocks are packaged with `clay build` (the `Dockerfile` is generated from the spec on each build; `clay dockerfile` prints it)
2. The Python clay library provides the `BlockWrapper` base class with `setup()`, `preprocess()`, `inference()`, `postprocess()` methods
3. Blocks run via the unified runner in `python/clay/runners/runner.py` (one-shot job)
4. Storage abstraction handles S3 (AWS, or MinIO via `AWS_ENDPOINT_URL`) / local file operations
5. Progress callbacks report execution status

### Registry System
- Go-based HTTP API server with Swagger docs
- PostgreSQL backend with sqlc-generated queries
- Manages block definitions, versions, and deployment metadata

### Key Components
- `python/clay/core.py` - `BlockWrapper` base class and execution logic
- `python/clay/runners/runner.py` - Runner that drives the block lifecycle
- `cmd/root.go` - CLI entry point and command structure
- `pkg/docker/docker.go` - Dockerfile generation from block specs

## Configuration

- Python linting: `ruff` (config in `pyproject.toml`)
- Type checking: `pyright` (config in `pyrightconfig.json`)
- Pre-commit hooks configured for formatting and validation
- Go version: 1.22+ (see `go.mod`)
- Python version: 3.10+ target

## Common Workflows

### Creating a New Block
1. `clay new <path>` (new or empty folder) or `clay init` (existing folder, keeps its files) - Generate project template; the block name is the folder name unless `--name` is given
2. Edit `clay.yaml` - Define inputs, outputs, and runtime
3. Implement block logic in `<block_name>/block.py`
4. Test locally with `python tests/test_block.py`
5. Package and run with `clay build` then `clay run`

### Registry Operations
- `clay block list` - List blocks in the registry
- `clay block describe <name>` - Show versions and details for a block
- `clay publish` - Build, push and register a block
- Point the CLI at a registry with `--clay-registry` or `CLAY_REGISTRY_HOST` (the flag wins when both are set)

## Testing Notes

- Python tests use pytest
- `make test` and `make test-go` do not run the registry service tests in `registry/`; run `make test-registry`. `make test-go` also skips `pkg/registry`
- Docker integration tests: `make test-integration`
- `examples/raster_vector_clipper` has a Docker Compose setup with MinIO for trying a block end to end

<!-- ## Coding style
While writing code you should follow the following books philosophy of software development:
- Clean Code by Robert C. Martin
- The Pragmatic Programmer by Andrew Hunt and David Thomas
- Code Complete by Steve McConnell -->
