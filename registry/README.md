# Clay Registry

The Clay Registry is a Go HTTP service that tracks Clay blocks, their versions,
and associated metadata. It is backed by PostgreSQL and exposes an OpenAPI /
Swagger-documented REST API.

Running a registry is optional — you can build and run Clay blocks without one.
When you do run one, the Clay CLI talks to it via `--clay-registry` (or
`CLAY_REGISTRY_HOST`).

## Prerequisites

- **Go** 1.22 or later
- **PostgreSQL** (any recent version; local install or Docker)
- Optional: **[golang-migrate](https://github.com/golang-migrate/migrate)** to run migrations by hand
- Optional (only needed when regenerating code):
  - **[swag](https://github.com/swaggo/swag)** — for Swagger doc generation
  - **[sqlc](https://sqlc.dev/)** — for SQL code generation
  - **[mockgen](https://github.com/uber-go/mock)** — for test mocks

Install the optional tooling when needed:

```bash
go install github.com/swaggo/swag/cmd/swag@latest
go install github.com/sqlc-dev/sqlc/cmd/sqlc@latest
go install go.uber.org/mock/mockgen@latest

# macOS
brew install golang-migrate
```

## Configuration

Copy the sample env file and adjust values for your environment (DB host,
port, credentials, service port):

```bash
make copy-config
```

This writes `app.env` from `sample.env`. Edit `app.env` to match your local
Postgres instance. The server needs `app.env` to start.

## Database

Create the database first. The default name is `clay_registry_dev`:

```bash
createdb clay_registry_dev
```

The database user must be able to run `CREATE EXTENSION "uuid-ossp"`, because
the first migration does that.

## Database Migrations

The server applies all pending migrations when it starts, using the settings
in `app.env`. You do not need to run them by hand.

To run them by hand, use these targets. They need golang-migrate. They do not
read `app.env`; they use the `DB_URL` in the `Makefile`. Override it if your
database differs:

```bash
make migrate-up                        # Apply all pending migrations
make migrate-down                      # Revert all migrations
make migrate-up DB_URL="postgresql://user:pass@host:5432/db?sslmode=disable"
make new-migration name=<name>         # Create a new migration pair
```

## Build and Run

```bash
make build   # Produces the `clay-registry` binary
make run     # Starts the service
```

Once the service is running, the Swagger UI is available at
`http://localhost:<port>/swagger/index.html` (port comes from `app.env`).

## Testing

```bash
make test
```

## Code Generation

```bash
make sqlc    # Regenerate typed DB access code from SQL queries
make mock    # Regenerate test mocks with mockgen
make swag    # Regenerate Swagger docs in api_docs/
```
