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

type modelRegistry struct {
	httpClient *http.Client
	host       string
	timeout    time.Duration
}

func NewModelRegistry(host string, timeout time.Duration) *modelRegistry {
	return &modelRegistry{
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

type PublishModelRequest struct {
	Name             string         `json:"name"`
	Kind             string         `json:"kind"`
	Type             string         `json:"type"`
	Version          string         `json:"version"`
	DockerImage      string         `json:"docker_image"`
	DocumentationURL string         `json:"documentation_url"`
	Specification    *Specification `json:"specification"`
}

type Data interface {
	any |
		Models |
		Model
}

type RegistryResponse[T Data] struct {
	Data  T      `json:"data"`
	Error string `json:"error"`
}

type Model struct {
	ID               string         `json:"id"`
	Name             string         `json:"name"`
	Kind             string         `json:"kind"`
	Type             string         `json:"type"`
	Version          string         `json:"version"`
	DockerImage      string         `json:"docker_image"`
	DocumentationURL string         `json:"documentation_url"`
	Specification    *Specification `json:"specification,omitempty"`
}

type Models []*Model

func (mr *modelRegistry) Publish(req *PublishModelRequest) error {
	url := mr.host + "/v1/blocks"

	body, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest(http.MethodPost, url, bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("failed to create HTTP request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := mr.httpClient.Do(httpReq)
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

	return fmt.Errorf("failed to publish model: %s, httpStatusCode: %v", respData.Error, resp.StatusCode)

}

func (mr *modelRegistry) ListBlocks() (Models, error) {
	url := mr.host + "/v1/blocks"
	httpReq, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request for list blocks: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := mr.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request for list blocks: %w", err)
	}
	defer resp.Body.Close()

	var respData *RegistryResponse[Models]
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return nil, fmt.Errorf("failed to unmarshall response for list blocks: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list blocks: %s", respData.Error)
	}

	return respData.Data, nil
}

func (mr *modelRegistry) GetBlockByName(name string) (Models, error) {
	url := mr.host + fmt.Sprintf("/v1/blocks/%s", name)
	httpReq, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request for list blocks with name %s: %w", name, err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := mr.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request for list blocks with name %s: %w", name, err)
	}
	defer resp.Body.Close()

	var respData *RegistryResponse[Models]
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return nil, fmt.Errorf("failed to unmarshall response for list blocks with name %s: %w", name, err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list blocks with name %s: %s", name, respData.Error)
	}

	return respData.Data, nil
}

func (mr *modelRegistry) GetBlockByNameAndVersion(name, version string) (*Model, error) {
	url := mr.host + fmt.Sprintf("/v1/blocks/%s/versions/%s", name, version)
	httpReq, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request for list block with name %s and version %s: %w", name, version, err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := mr.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request for list block with name %s and version %s: %w", name, version, err)
	}
	defer resp.Body.Close()

	var respData *RegistryResponse[Model]
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return nil, fmt.Errorf("failed to unmarshall response for list block with name %s and version %s: %w", name, version, err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list block with name %s and version %s: %s", name, version, respData.Error)
	}

	return &respData.Data, nil
}
