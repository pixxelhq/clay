---
title: Clay Registry
order: 7
---

# Clay Registry

The Clay Registry is an optional HTTP service for tracking blocks, their
versions, and associated metadata. It decouples block development from block
execution — block authors publish new versions to the registry, and any
orchestrator or consumer can query it to discover available blocks.

Using a registry is **optional**. You can build and run Clay blocks as plain
Docker containers without ever publishing to a registry.

## What the registry stores

- Block definitions (name, kind, type, description)
- Versions of each block
- Docker image reference for each version
- Documentation and thumbnail URLs
- Block specification snapshots

The registry is a Go HTTP service backed by PostgreSQL. Source lives under
[`registry/`](https://github.com/pixxelhq/clay-framework/tree/main/registry).

## Running a registry locally

The registry ships with a `Makefile` that covers the common dev workflow. From
the `registry/` directory:

```bash
# Copy sample env and adjust DB credentials if needed
make copy-config

# Apply database migrations to a running Postgres
make migrate-up

# Build and run the server
make build
make run
```

Once the service is running, the OpenAPI/Swagger UI is available at
`http://localhost:<port>/swagger/index.html` (port is configured via
`app.env`).

See [`registry/README.md`](https://github.com/pixxelhq/clay-framework/blob/main/registry/README.md)
for migration, testing, and `sqlc` code generation details.

## CLI commands that talk to a registry

The Clay CLI speaks to any registry implementation that matches the public API.
Point it at your instance with the `--clay-registry` flag or the
`CLAY_REGISTRY_HOST` environment variable.

| Command | Purpose |
|---------|---------|
| `clay publish` | Publish the current block (builds + pushes the image + registers the version). |
| `clay block list` | List blocks in the registry. Supports `-n, --name` and `-v, --version` filters. |
| `clay block describe <name>` | Show details for a block (optionally a specific `-v, --version`). |

See the [CLI Reference](cli-reference.md) for the complete flag list.

## Publishing a block

```bash
# From inside your block project
clay publish \
  --clay-registry https://clay-registry.example.com \
  --docker-registry registry.example.com
```

`clay publish` will:

1. Build the block's Docker image using the spec in `clay.yaml`.
2. Push the image to the configured Docker registry.
3. Register the new block version with the Clay registry.
