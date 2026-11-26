# Clay

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pixxel-clay.svg)](https://pypi.org/project/pixxel-clay/)
[![Tests](https://github.com/pixxelhq/clay/actions/workflows/test.yml/badge.svg)](https://github.com/pixxelhq/clay/actions/workflows/test.yml)
[![Docs](https://github.com/pixxelhq/clay/actions/workflows/deploy-docs.yaml/badge.svg)](https://pixxelhq.github.io/clay/)

**Clay** is an open-source framework for packaging ML models as deployable,
declaratively-configured **blocks**. You describe your model — its inputs,
outputs, GPU needs, and build environment — in a single YAML file, and
Clay takes care of the rest: generating a `Dockerfile`, building the container,
and registering the block for an orchestrator to run.

Clay lets you focus on model logic and keeps deployment concerns out of your
code.

---

## Features

- **Declarative block specs** — describe inputs, outputs, GPU use, and the build
  in one YAML file.
- **Automatic container builds** — Clay generates a `Dockerfile` and builds an
  image tailored to your spec.
- **Job runner** — runs a block as a one-shot job, locally with `clay run` or
  under an orchestrator.
- **Storage** — blocks read and write `s3://` paths on AWS S3, or on MinIO and
  other S3-compatible stores when `AWS_ENDPOINT_URL` is set; local filesystem
  for development. `clay block assets` supports AWS S3 URLs only.
- **Optional block registry** — an HTTP service for tracking block versions
  and metadata, which you run yourself (see [Registry service](https://pixxelhq.github.io/clay/registry/)).
- **Typed I/O** — first-class support for raster, vector, and scalar data
  types via the [`pixxel-datatypes`](proto/) schema package.

## Installation

### CLI — Homebrew (recommended)

```bash
brew tap pixxelhq/tap
brew install clay --formula
```

### CLI — Pre-built binary

Download the archive for your platform from
[GitHub Releases](https://github.com/pixxelhq/clay/releases), then put the
`clay` binary somewhere on your `PATH`:

```bash
# macOS (Apple Silicon); set VERSION to the latest release, without the "v"
VERSION=1.5.0
curl -L https://github.com/pixxelhq/clay/releases/download/v${VERSION}/clay_${VERSION}_darwin_arm64.tar.gz | tar -xz clay
sudo mv clay /usr/local/bin/
```

Archives are named `clay_<version>_<os>_<arch>.tar.gz`, for `darwin`, `linux`
and `windows` on `amd64` and `arm64`.

### Python SDK (PyPI)

```bash
pip install pixxel-clay
# or, with uv
uv pip install pixxel-clay
```

Requires Python **3.10+**. Clay does not need GDAL itself. If your block uses
GDAL, install it locally for testing; in the image, `build.gdal: true` in
`clay.yaml` provides it.

### From source

```bash
git clone https://github.com/pixxelhq/clay.git
cd clay
make go-binaries       # builds the CLI into ./bin
make package           # builds the Python sdist+wheel into python/dist
```

## Quickstart

```bash
# 1. Scaffold a new block
clay new my-block

cd my-block

# 2. Set up a Python environment and install dependencies
uv venv && source .venv/bin/activate
uv pip install -r requirements-dev.txt

# 3. Edit the generated spec and block code
#    - clay.yaml          : inputs, outputs, build settings
#    - my_block/block.py  : setup/preprocess/inference/postprocess

# 4. Test locally
python tests/test_block.py

# 5. Package into a container
clay build
```

Full walkthrough: [**Getting Started**](https://pixxelhq.github.io/clay/getting-started/).

## CLI overview

| Command | What it does |
|---|---|
| `clay new <path>` | Scaffold a new block project in `<path>`, which must not exist or be empty |
| `clay init` | Make the current directory a block project, keeping the files already in it |
| `clay build` | Build a Docker image locally from `clay.yaml` (generates the `Dockerfile` on each build) |
| `clay dockerfile` | Print the `Dockerfile` that `clay build` generates |
| `clay run [image]` | Run a block image locally; without `image`, runs `<name>:<version>` from `clay.yaml` |
| `clay push [image]` | Push a block image to a Docker registry; without `image`, pushes `<name>:<version>` from `clay.yaml` to `--docker-registry` or `CLAY_DOCKER_REGISTRY` |
| `clay publish` | Build, push, and register a block in one command |
| `clay block list --clay-registry <url>` | List blocks in a Clay registry |
| `clay block describe <name> --clay-registry <url>` | Show versions and details for a block |
| `clay block assets upload <path> --url <s3-url>` | Upload block assets to S3 |
| `clay block assets list --url <s3-url>` | List assets at a storage URL |
| `clay block assets download --url <s3-url> -o <path>` | Download a block asset |

Full reference: [**CLI Reference**](https://pixxelhq.github.io/clay/cli-reference/).

## Documentation

- [Overview](https://pixxelhq.github.io/clay/overview/)
- [Getting started](https://pixxelhq.github.io/clay/getting-started/)
- [Block specification](https://pixxelhq.github.io/clay/spec/)
- [Block development guide](https://pixxelhq.github.io/clay/block-development/)
- [Block assets](https://pixxelhq.github.io/clay/block-assets/)
- [Registry service](https://pixxelhq.github.io/clay/registry/)
- [CLI reference](https://pixxelhq.github.io/clay/cli-reference/)

## Repository layout

```
cmd/            Go CLI commands
pkg/            Go packages (config, docker, registry client, storage, catalog)
python/clay/    Python runtime library used by packaged blocks
proto/          Protobuf datatypes + generated Python/Go bindings
registry/       Go HTTP registry service (PostgreSQL backend)
api/bootstrap/  Project templates for clay new and clay init
examples/       Sample blocks and Docker Compose setups
mkdocs/         Documentation site source
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for dev
setup, testing, and pull-request guidelines. For security issues, please
follow [SECURITY.md](SECURITY.md).

## License

Clay is licensed under the [Apache License 2.0](LICENSE).
