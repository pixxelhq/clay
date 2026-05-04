DB_URL=postgresql://postgres:postgres@localhost:5432/clay_registry_dev?sslmode=disable

build:
	go build -o clay-registry cmd/app/registry.go

test:
	go test ./...

run:
	go run cmd/app/registry.go

copy-config:
	cp ./sample.env ./app.env

migrate-up:
	migrate -path ./internal/store/migrations -database "$(DB_URL)" -verbose up

migrate-down:
	migrate -path ./internal/store/migrations -database "$(DB_URL)" -verbose down

new-migration:
	migrate create -ext sql -dir internal/store/migrations -seq $(name)

sqlc:
	sqlc generate

mock:
	mockgen --build_flags=--mod=mod -package mock_store -destination internal/store/mock/store.go github.com/pixxelhq/clay-framework/registry/internal/store/sqlc Store
	mockgen --build_flags=--mod=mod -package mock_block -destination pkg/block/mock/block.go github.com/pixxelhq/clay-framework/registry/pkg/block Service

swag:
	swag init -g cmd/app/registry.go --overridesFile override.swag -o api_docs

swag-fmt:
	swag fmt