# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Clay is an open-source framework for packaging ML models as deployable blocks. It consists of:
- **Clay CLI** (Go): Command-line tool for creating projects, building containers, and managing model registry
- **Clay Python package**: Runtime library used by packaged models for execution

## Project Structure

The repository is organized as follows:

- `cmd/` - Go CLI commands (create, list, publish, etc.)
- `pkg/` - Go packages for config, docker, registry, logging
- `python/clay/` - Python runtime library
  - `runners/` - Model execution engines (HTTP, job-based)
  - `storage/` - File system abstractions (S3, local)
  - `callback/` - Progress reporting mechanisms
- `api/` - Go backend services
- `registry/` - Model registry service with PostgreSQL backend
- `examples/` - Sample models and Docker Compose setups
- `mkdocs/` - Documentation site

## Development Commands

### Testing
- `make test` - Run all tests (Go + Python)
- `make test-go` - Go tests only (excludes registry)
- `make test-python` - Python tests only (`cd python; pytest -vv`)
- `make test-registry` - Registry service tests

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
- `make test-with-runner` - Test with Kubernetes executor
- `make test-with-runnerv2` - Test with Argo executor
- `make tear-down` - Clean up Docker Compose test environment

## Architecture

### Block Execution Flow
1. Blocks are packaged with `clay build` (a `Dockerfile` is generated from the spec when one doesn't already exist)
2. The Python clay library provides the `BlockWrapper` base class with `setup()`, `preprocess()`, `inference()`, `postprocess()` methods
3. Blocks run via the unified runner in `python/clay/runners/runner.py` (HTTP server or batch job mode)
4. Storage abstraction handles S3-compatible / local file operations
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
- Type checking: `pyright` (config in `pyproject.toml`)
- Pre-commit hooks configured for formatting and validation
- Go version: 1.22+ (see `go.mod`)
- Python version: 3.10+ target

## Common Workflows

### Creating a New Block
1. `clay new <outputDir> <BlockName>` - Generate project template
2. Edit `clay.yaml` - Define inputs, outputs, and runtime
3. Implement block logic in `src/block.py`
4. Test locally with `python tests/test_block.py`
5. Package and run with `clay build` then `clay run`

### Registry Operations
- `clay list block` - List available models
- `clay add block <specFile>` - Register new model
- `clay update block <specFile>` - Update existing model
- Use `-e dev|stg|prod` to specify environment

## Testing Notes

- Python tests use pytest with asyncio support
- Go tests exclude registry by default (separate DB required)
- Integration tests available with Docker Compose setup
- Model testing requires MinIO S3 storage backend

<!-- ## Coding style
While writing code you should follow the following books philosophy of software development:
- Clean Code by Robert C. Martin
- The Pragmatic Programmer by Andrew Hunt and David Thomas
- Code Complete by Steve McConnell -->
