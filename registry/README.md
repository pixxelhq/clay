# Clay Registry

This project is a registry service built using Go. It provides a RESTful API for managing registry entries.

## Tools

mockgen: 

`go install github.com/golang/mock/mockgen@latest`

swag: 

`go install github.com/swaggo/swag/cmd/swag@latest`

sqlc:

`go install github.com/kyleconroy/sqlc/cmd/sqlc@latest`

migrate (macOS):

`brew install golang-migrate`

## Configuration

The project uses environment variables for configuration. You can copy the sample configuration file to `app.env` using the following command:
```
make copy-config
```

## Database Migrations
To apply database migrations, run the following command:
```
make migrate-up
```
To revert the last migration, use:
```
make migrate-down
```
To create a new migration, use:
```
make new-migration name=<migration_name>
```
Replace `<migration_name>` with the actual name of your migration.

## Testing

To run tests, execute the following command:
```
make test
```
This will run all tests in the project.

## Building and Running

To build the project, run the following command:
```
make build
```
This will create an executable named `clay-registry`.

To run the project, execute the following command:
```
make run
```
This will start the registry service.

## SQL Code Generation

To generate SQL code, run the following command:
```
make sqlc
```
This will generate SQL code based on the project's schema.
