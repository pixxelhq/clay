package http

import (
	"encoding/json"
	"time"
)

type Data interface {
	any |
		CreateBlockResponse |
		GetLatestBlocksResponse |
		GetBlocksByNameResponse
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
	APIVersion string          `json:"apiVersion"`
	Author     string          `json:"author"`
	Tags       []string        `json:"tags"`
	Parameters json.RawMessage `json:"parameters"`
	Inputs     json.RawMessage `json:"inputs"`
	Outputs    json.RawMessage `json:"outputs"`
	Build      json.RawMessage `json:"build"`
	GPU        bool            `json:"gpu"`
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
	ID               string         `json:"id"`
	Name             string         `json:"name"`
	Version          string         `json:"version"`
	Type             string         `json:"type"`
	DockerImage      string         `json:"docker_image"`
	DocumentationURL string         `json:"documentation_url"`
	CreatedAt        time.Time      `json:"created_at"`
	UpdatedAt        time.Time      `json:"updated_at"`
	Specification    *Specification `json:"specification"`
}

type GetLatestBlocksResponse []*GetLatestBlock
type GetLatestBlock struct {
	ID               string         `json:"id"`
	Name             string         `json:"name"`
	Version          string         `json:"version"`
	Type             string         `json:"type"`
	Kind             string         `json:"kind"`
	DockerImage      string         `json:"docker_image"`
	DocumentationURL string         `json:"documentation_url"`
	CreatedAt        time.Time      `json:"created_at"`
	UpdatedAt        time.Time      `json:"updated_at"`
	Specification    *Specification `json:"specification,omitempty"`
}

type GetBlocksByNameResponse []*GetBlockByNameAndVersion

type GetBlockByNameAndVersion struct {
	ID               string         `json:"id"`
	Name             string         `json:"name"`
	Version          string         `json:"version"`
	Kind             string         `json:"kind"`
	Type             string         `json:"type"`
	DockerImage      string         `json:"docker_image"`
	DocumentationURL string         `json:"documentation_url"`
	CreatedAt        time.Time      `json:"created_at"`
	UpdatedAt        time.Time      `json:"updated_at"`
	Specification    *Specification `json:"specification"`
}
