# Contributing to Clay

Thanks for your interest in contributing to Clay! This guide covers everything
you need to set up a development environment, make changes, and open a pull
request.

If you are reporting a security issue, please read [SECURITY.md](SECURITY.md)
first — do **not** open a public issue for vulnerabilities.

## Prerequisites

### System Requirements

- **Go** 1.22 or later
- **Python** 3.10 or later
- **Docker** (for building images and running integration tests)
- **[uv](https://docs.astral.sh/uv/)** (preferred Python installer) or `pip`
- **pre-commit** (`pip install pre-commit` or `brew install pre-commit`)

No internal credentials, VPN access, or private package indexes are required.
All dependencies are fetched from public PyPI and the public Go module proxy.

## Getting Started

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/clay.git
cd clay
```

### 2. Install development dependencies

`make init` and `make init-requirements` install with `uv pip install`, which
needs a virtual environment. Create and activate one first:

```bash
python3 -m venv .venv && source .venv/bin/activate
make init
```

If `uv` is not on your `PATH`, `make init` installs it with uv's install
script. `make init` installs the Python dev requirements, sets up pre-commit
hooks, and configures commit-message hooks.

### 3. Install project requirements

```bash
make init-requirements
```

This installs the local `pixxel-datatypes` package from `proto/python` and the development requirements.

## Development Workflow

### Build

```bash
make package        # Build the Python distribution (sdist + wheel) under python/dist/
make go-binaries    # Build the Clay CLI for macOS / Linux / Windows under bin/
```

### Test

```bash
make test           # Go tests of the root module and Python tests (not registry/)
make test-python    # Python only
make test-go        # Go tests of the root module, except pkg/registry (the CLI's registry client)
make test-registry  # Registry service tests; registry/ is a separate Go module
```

Docker integration tests (need a running Docker daemon):

```bash
make test-integration
```

### Format and lint

```bash
make format       # ruff format + pre-commit hooks
make pre-commit   # Run the pre-commit hooks manually
```

Run these before opening a pull request. CI runs `ruff check`, pyright, the tests and a docs build.

### Documentation

Clay's docs live under [`mkdocs/`](mkdocs/).

```bash
make build-docs         # Build the site
make serve-docs         # Serve locally at http://localhost:8000
make spell-check-docs   # Spell-check markdown
```

## Submitting a Pull Request

1. Create a topic branch off `main` (`git checkout -b fix/short-description`).
2. Make your changes. Keep commits focused — one logical change per commit.
3. Add or update tests for any behavior change.
4. Add an entry to [`CHANGELOG.md`](CHANGELOG.md) under
   `## Unreleased`, under `### Upgrading`, `### New Features`, `### Bug Fixes` or
   `### Breaking Changes` as appropriate.
5. Run `make format` and `make test` locally and make sure they pass.
6. Push your branch and open a pull request against `main`. Fill out the PR
   template.
7. Address review feedback by pushing additional commits to the same branch —
   avoid force-pushing once reviewers have started looking at the diff.

## Reporting Bugs and Requesting Features

Please use the GitHub issue templates:

- [Bug report](.github/ISSUE_TEMPLATE/bug_report.md)
- [Feature request](.github/ISSUE_TEMPLATE/feature_request.md)

## License

By contributing to Clay, you agree that your contributions will be licensed
under the [Apache License 2.0](LICENSE).
