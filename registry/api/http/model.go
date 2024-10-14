package http

import (
	"encoding/json"
	"time"
)

type Data interface {
	any |
		CreateBlockResponse |
		[]*GetLatestBlock
}

type Error struct {
	Message string `json:"message"`
	Code    string `json:"code"`
}

type RegistryResponse[T Data] struct {
	Data  T      `json:"data"`
	Error string `json:"error"`
}

type Specification struct {
	Version     string          `json:"apiVersion"`
	Title       string          `json:"title"`
	Description string          `json:"description"`
	Author      string          `json:"author"`
	Tags        []string        `json:"tags"`
	Parameters  json.RawMessage `json:"parameters"`
	Inputs      json.RawMessage `json:"inputs"`
	Outputs     json.RawMessage `json:"outputs"`
	Build       json.RawMessage `json:"build"`
}

type CreateBlockRequest struct {
	Name             string         `json:"name"`
	Version          string         `json:"version"`
	Kind             string         `json:"kind"`
	Type             string         `json:"type"`
	DockerImage      string         `json:"docker_image"`
	DocumentationURL string         `json:"documentation_url"`
	Specification    *Specification `json:"specification"`
}

type CreateBlockResponse struct {
	ID            string         `json:"id"`
	Name          string         `json:"name"`
	Version       string         `json:"version"`
	Type          string         `json:"type"`
	CreatedAt     time.Time      `json:"created_at"`
	UpdatedAt     time.Time      `json:"updated_at"`
	Specification *Specification `json:"specification"`
}

type GetLatestBlock struct {
	ID            string         `json:"id"`
	Name          string         `json:"name"`
	Version       string         `json:"version"`
	Type          string         `json:"type"`
	CreatedAt     time.Time      `json:"created_at"`
	UpdatedAt     time.Time      `json:"updated_at"`
	Specification *Specification `json:"specification"`
}
