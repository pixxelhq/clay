# Clay

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pixxel-clay.svg)](https://pypi.org/project/pixxel-clay/)
[![Tests](https://github.com/pixxelhq/clay-framework/actions/workflows/test.yml/badge.svg)](https://github.com/pixxelhq/clay-framework/actions/workflows/test.yml)
[![Docs](https://github.com/pixxelhq/clay-framework/actions/workflows/deploy-docs.yaml/badge.svg)](https://pixxelhq.github.io/clay-framework/)

**Clay** is an open-source framework for packaging ML models as deployable,
declaratively-configured **blocks**. You describe your model — its inputs,
outputs, resource needs, and runtime environment — in a single YAML file, and
Clay takes care of the rest: generating a `Dockerfile`, building the container,
and registering the block for an orchestrator to run.

Clay lets you focus on model logic and keeps deployment concerns out of your
code.

---

## Features

- **Declarative block specs** — describe inputs, outputs, compute, and runtime
  in one YAML file.
- **Automatic container builds** — Clay generates a `Dockerfile` and builds an
  image tailored to your spec.
- **HTTP and batch runners** — serve blocks as HTTP endpoints or run them as
  one-shot jobs, with the same block code.
- **Pluggable storage** — S3-compatible storage (including MinIO) out of the
  box; local filesystem for development.
- **Optional block registry** — an HTTP service for tracking block versions
  and metadata, runnable via Docker Compose.
- **Typed I/O** — first-class support for raster, vector, and scalar data
  types via the [`pixxel-datatypes`](proto/) schema package.

## Installation

### CLI (Go binary)

Download the latest release for your platform from
[GitHub Releases](https://github.com/pixxelhq/clay-framework/releases), then put the
binary somewhere on your `PATH`:

```bash
# macOS (Apple Silicon)
curl -L https://github.com/pixxelhq/clay-framework/releases/latest/download/clay-<version>-macosx-arm64 -o /usr/local/bin/clay
chmod +x /usr/local/bin/clay
```

### Python SDK (PyPI)

```bash
pip install pixxel-clay
# or, with uv
uv pip install pixxel-clay
```

Requires Python **3.10+**. `GDAL` must be installed and discoverable on your
system for blocks that work with raster data.

### From source

```bash
git clone https://github.com/pixxelhq/clay-framework.git
cd clay
make go-binaries       # builds the CLI into ./bin
make package           # builds the Python sdist+wheel into python/dist
```

## Quickstart

```bash
# 1. Scaffold a new block
clay new ./my-block MyBlock

cd ./my-block

# 2. Set up a Python environment and install dependencies
uv venv && source .venv/bin/activate
uv pip install pixxel-clay

# 3. Edit the generated spec and block code
#    - specifications/block_specification_dev.yaml : inputs, outputs, resources
#    - src/block.py                                : setup/preprocess/inference/postprocess

# 4. Test locally
python src/test_block.py

# 5. Package into a container
clay build
```

Full walkthrough: [**Getting Started**](https://pixxelhq.github.io/clay-framework/getting-started/).

## CLI overview

| Command | What it does |
|---|---|
| `clay new <path> <name>` | Scaffold a new block project |
| `clay build` | Build a Docker image from `clay.yaml` (generates a `Dockerfile` if needed) |
| `clay run <image>` | Run a block image locally |
| `clay push <image>` | Push a block image to a Docker registry |
| `clay publish` | Build, push, and register a block in one command |
| `clay block list` | List blocks in a Clay registry |
| `clay block describe <name>` | Show versions and details for a block |
| `clay block assets upload <path> --url <s3-url>` | Upload block assets to S3 |
| `clay block assets list --url <s3-url>` | List assets at a storage URL |
| `clay block assets download --url <s3-url> -o <path>` | Download a block asset |

Full reference: [**CLI Reference**](https://pixxelhq.github.io/clay-framework/cli-reference/).

## Documentation

- [Overview](https://pixxelhq.github.io/clay-framework/overview/)
- [Getting started](https://pixxelhq.github.io/clay-framework/getting-started/)
- [Block specification](https://pixxelhq.github.io/clay-framework/spec/)
- [Block development guide](https://pixxelhq.github.io/clay-framework/block-development/)
- [Block assets](https://pixxelhq.github.io/clay-framework/block-assets/)
- [Registry service](https://pixxelhq.github.io/clay-framework/registry/)
- [CLI reference](https://pixxelhq.github.io/clay-framework/cli-reference/)

## Repository layout

```
cmd/            Go CLI commands
pkg/            Go packages (config, docker, registry client, logging)
python/clay/    Python runtime library used by packaged blocks
proto/          Protobuf datatypes + generated Python/Go bindings
registry/       Go HTTP registry service (PostgreSQL backend)
api/            Supporting Go backend services
examples/       Sample blocks and Docker Compose setups
mkdocs/         Documentation site source
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for dev
setup, testing, and pull-request guidelines. For security issues, please
follow [SECURITY.md](SECURITY.md).

## License

Clay is licensed under the [Apache License 2.0](LICENSE).
