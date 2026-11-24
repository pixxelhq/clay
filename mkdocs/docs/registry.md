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

- Block definitions (name, kind, type)
- Versions of each block
- Docker image reference for each version
- The URL of the published `catalog.yaml` (the catalog itself is not stored)
- Block specification snapshots

The registry is a Go HTTP service backed by PostgreSQL. Source lives under
[`registry/`](https://github.com/pixxelhq/clay/tree/main/registry).

## Running a registry locally

You need a running PostgreSQL server with an empty database. The default
name is `clay_registry_dev` (see `sample.env`). The database user must be able
to run `CREATE EXTENSION "uuid-ossp"`, because the first migration does that.

```bash
createdb clay_registry_dev
```

The registry ships with a `Makefile` that covers the common dev workflow. From
the `registry/` directory:

```bash
# Copy sample env and adjust DB credentials if needed
make copy-config

# Start the server from source (go run)
make run
```

`make run` does not use a built binary. `make build` writes a `clay-registry`
binary; start it from the `registry/` directory (`./clay-registry`), because the
server reads `app.env` and the migrations relative to the current directory.

The server applies database migrations when it starts. You do not need to run
them by hand. `make migrate-up` is optional. It needs
[golang-migrate](https://github.com/golang-migrate/migrate) and does not read
`app.env`; it uses the `DB_URL` in the `Makefile`. Override it if your database
differs: `make migrate-up DB_URL="postgresql://user:pass@host:5432/db?sslmode=disable"`.

Once the service is running, the OpenAPI/Swagger UI is available at
`http://localhost:<port>/swagger/index.html` (port is configured via
`app.env`).

See [`registry/README.md`](https://github.com/pixxelhq/clay/blob/main/registry/README.md)
for migration, testing, and `sqlc` code generation details.

## CLI commands that talk to a registry

The CLI calls the registry's HTTP API under `/v1/blocks`. Point it at your
instance with the `--clay-registry` flag. `clay publish` also reads the
`CLAY_REGISTRY_HOST` environment variable; `clay block list` and
`clay block describe` do not, so pass `--clay-registry` to them.

| Command | Purpose |
|---------|---------|
| `clay publish` | Publish the current block (builds + pushes the image + registers the version). |
| `clay block list` | Without flags, list the latest version of each block. `-n, --name` lists all versions of a block; `-v, --version` with `--name` shows one version. |
| `clay block describe <name>` | List all versions of a block, or show one with `-v, --version`. |

See the [CLI Reference](cli-reference.md) for the complete flag list.

## Publishing a block

```bash
# From inside your block project
clay publish \
  --clay-registry https://clay-registry.example.com \
  --docker-registry registry.example.com
```

`clay publish` will:

1. Check that the block version is not already in the Clay registry. If it is, it stops.
   The check uses `version` as written in `clay.yaml`, and the registry stores
   versions without a leading `v`, so a `v`-prefixed version such as `v0.0.1`
   passes this check even when it is published (see
   [Publish](cli-reference.md#publish)).
2. Build the block's Docker image. It uses `-f/--file` if given, else
   `./Dockerfile` if it exists, else a Dockerfile generated from `clay.yaml`.
3. Push the image to the configured Docker registry.
4. Register the new block version with the Clay registry. The registry stores
   the version in semantic-version form (`v0.0.1` becomes `0.0.1`) and rejects
   a version that is already published or is not a semantic version.
