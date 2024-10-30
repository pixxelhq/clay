FROM golang:1.22.1-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o clay_registry cmd/app/registry.go

FROM alpine:3.16
WORKDIR /app
COPY  ./internal/store/migrations ./internal/store/migrations
COPY --from=builder /app/clay_registry .
COPY sample.env app.env
EXPOSE 8080
CMD ["./clay_registry"]
