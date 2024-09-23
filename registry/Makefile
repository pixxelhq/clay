DB_URL=postgresql://postgres:postgres@localhost:5432/clay_registry_dev?sslmode=disable

build:
	go build -o clay-registry cmd/app/registry.go

test:
	go test -v ./...

run:
	go run cmd/app/registry.go

copy-config:
	cp ./sample.env ./app.env

migreate-up:
	migrate -path internal/store/migrations -database "$(DB_URL)" -verbose up

migrate-down:
	migrate -path internal/store/migrations -database "$(DB_URL)" -verbose down

new-migration:
	migrate create -ext sql -dir internal/store/migrations -seq $(name)

sqlc:
	sqlc generate