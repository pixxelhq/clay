package registry

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"time"
)

var (
	ErrAlreadyExists = errors.New("block_already_exists")
)

// Registry is a client for the Clay block registry HTTP API.
type Registry struct {
	httpClient *http.Client
	host       string
	timeout    time.Duration
}

// New returns a Registry client pointed at host with the given request timeout.
func New(host string, timeout time.Duration) *Registry {
	return &Registry{
		host:    host,
		timeout: timeout,
		httpClient: &http.Client{
			Timeout: timeout,
		},
	}
}

type Specification struct {
	APIVersion string          `json:"apiVersion"`
	Title      string          `json:"title"`
	Author     string          `json:"author"`
	Tags       []string        `json:"tags"`
	Parameters json.RawMessage `json:"parameters"`
	Inputs     json.RawMessage `json:"inputs"`
	Outputs    json.RawMessage `json:"outputs"`
	Build      json.RawMessage `json:"build"`
	ENV        json.RawMessage `json:"env"`
	Gpu        bool            `json:"gpu"`
}

type PublishBlockRequest struct {
	Name             string         `json:"name"`
	Kind             string         `json:"kind"`
	Type             string         `json:"type"`
	Version          string         `json:"version"`
	DockerImage      string         `json:"docker_image"`
	DocumentationURL string         `json:"documentation_url"`
	ThumbnailURL     string         `json:"thumbnail_url"`
	Specification    *Specification `json:"specification"`
	// Catalog carries the structured catalog documentation (post media-rewrite)
	// when the model repo declares a catalog.yaml.
	Catalog json.RawMessage `json:"catalog,omitempty"`
}

type Data interface {
	any |
		Blocks |
		Block
}

type RegistryResponse[T Data] struct {
	Data  T      `json:"data"`
	Error string `json:"error"`
}

type Block struct {
	ID               string         `json:"id"`
	Name             string         `json:"name"`
	Kind             string         `json:"kind"`
	Type             string         `json:"type"`
	Version          string         `json:"version"`
	DockerImage      string         `json:"docker_image"`
	DocumentationURL string         `json:"documentation_url"`
	ThumbnailURL     string         `json:"thumbnail_url"`
	Specification    *Specification `json:"specification,omitempty"`
}

type Blocks []*Block

func (r *Registry) Publish(req *PublishBlockRequest) error {
	url := r.host + "/v1/blocks"

	body, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest(http.MethodPost, url, bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("failed to create HTTP request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := r.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusCreated {
		return nil
	}

	if resp.StatusCode == http.StatusConflict {
		return ErrAlreadyExists
	}

	var respData RegistryResponse[any]
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return fmt.Errorf("failed to decode response: %w", err)
	}

	return fmt.Errorf("failed to publish block: %s, httpStatusCode: %v", respData.Error, resp.StatusCode)

}

func (r *Registry) ListBlocks() (Blocks, error) {
	url := r.host + "/v1/blocks"
	httpReq, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request for list blocks: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := r.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request for list blocks: %w", err)
	}
	defer resp.Body.Close()

	var respData *RegistryResponse[Blocks]
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return nil, fmt.Errorf("failed to unmarshall response for list blocks: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list blocks: %s", respData.Error)
	}

	return respData.Data, nil
}

func (r *Registry) GetBlockByName(name string) (Blocks, error) {
	url := r.host + fmt.Sprintf("/v1/blocks/%s", name)
	httpReq, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request for list blocks with name %s: %w", name, err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := r.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request for list blocks with name %s: %w", name, err)
	}
	defer resp.Body.Close()

	var respData *RegistryResponse[Blocks]
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return nil, fmt.Errorf("failed to unmarshall response for list blocks with name %s: %w", name, err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list blocks with name %s: %s", name, respData.Error)
	}

	return respData.Data, nil
}

func (r *Registry) GetBlockByNameAndVersion(name, version string) (*Block, error) {
	url := r.host + fmt.Sprintf("/v1/blocks/%s/versions/%s", name, version)
	httpReq, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request for list block with name %s and version %s: %w", name, version, err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := r.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request for list block with name %s and version %s: %w", name, version, err)
	}
	defer resp.Body.Close()

	var respData *RegistryResponse[Block]
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return nil, fmt.Errorf("failed to unmarshall response for list block with name %s and version %s: %w", name, version, err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list block with name %s and version %s: %s", name, version, respData.Error)
	}

	return &respData.Data, nil
}
