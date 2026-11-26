package registry

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/url"
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
	Name          string         `json:"name"`
	Kind          string         `json:"kind"`
	Type          string         `json:"type"`
	Version       string         `json:"version"`
	DockerImage   string         `json:"docker_image"`
	Specification *Specification `json:"specification"`
	CatalogURL    string         `json:"catalog_url,omitempty"`
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
	ID            string         `json:"id"`
	Name          string         `json:"name"`
	Kind          string         `json:"kind"`
	Type          string         `json:"type"`
	Version       string         `json:"version"`
	DockerImage   string         `json:"docker_image"`
	CatalogURL    string         `json:"catalog_url,omitempty"`
	Specification *Specification `json:"specification,omitempty"`
}

type Blocks []*Block

func (r *Registry) Publish(req *PublishBlockRequest) error {
	if err := r.checkHost(); err != nil {
		return err
	}

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
		return unreachableError(r.host, err)
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
		return notARegistryError(url, resp.StatusCode, err)
	}

	return fmt.Errorf("failed to publish block: %s, httpStatusCode: %v", respData.Error, resp.StatusCode)

}

func (r *Registry) ListBlocks() (Blocks, error) {
	if err := r.checkHost(); err != nil {
		return nil, err
	}

	url := r.host + "/v1/blocks"
	httpReq, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request for list blocks: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := r.httpClient.Do(httpReq)
	if err != nil {
		return nil, unreachableError(r.host, err)
	}
	defer resp.Body.Close()

	var respData *RegistryResponse[Blocks]
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return nil, notARegistryError(url, resp.StatusCode, err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list blocks: %s", respData.Error)
	}

	return respData.Data, nil
}

func (r *Registry) GetBlockByName(name string) (Blocks, error) {
	if err := r.checkHost(); err != nil {
		return nil, err
	}

	url := r.host + fmt.Sprintf("/v1/blocks/%s", name)
	httpReq, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request for list blocks with name %s: %w", name, err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := r.httpClient.Do(httpReq)
	if err != nil {
		return nil, unreachableError(r.host, err)
	}
	defer resp.Body.Close()

	var respData *RegistryResponse[Blocks]
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return nil, notARegistryError(url, resp.StatusCode, err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list blocks with name %s: %s", name, respData.Error)
	}

	return respData.Data, nil
}

func (r *Registry) GetBlockByNameAndVersion(name, version string) (*Block, error) {
	if err := r.checkHost(); err != nil {
		return nil, err
	}

	url := r.host + fmt.Sprintf("/v1/blocks/%s/versions/%s", name, version)
	httpReq, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request for list block with name %s and version %s: %w", name, version, err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := r.httpClient.Do(httpReq)
	if err != nil {
		return nil, unreachableError(r.host, err)
	}
	defer resp.Body.Close()

	var respData *RegistryResponse[Block]
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return nil, notARegistryError(url, resp.StatusCode, err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list block with name %s and version %s: %s", name, version, respData.Error)
	}

	return &respData.Data, nil
}

func (r *Registry) VersionExists(name, version string) (bool, error) {
	if err := r.checkHost(); err != nil {
		return false, err
	}

	url := r.host + fmt.Sprintf("/v1/blocks/%s/versions/%s", name, version)
	httpReq, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return false, fmt.Errorf("failed to create HTTP request for block %s version %s: %w", name, version, err)
	}

	resp, err := r.httpClient.Do(httpReq)
	if err != nil {
		return false, unreachableError(r.host, err)
	}
	defer resp.Body.Close()

	switch resp.StatusCode {
	case http.StatusOK:
		return true, nil
	case http.StatusNotFound:
		var notFound RegistryResponse[any]
		if err := json.NewDecoder(resp.Body).Decode(&notFound); err != nil || notFound.Error == "" {
			return false, notARegistryError(url, resp.StatusCode, errors.New("no registry error in the response"))
		}
		return false, nil
	}

	var respData RegistryResponse[any]
	_ = json.NewDecoder(resp.Body).Decode(&respData)
	return false, fmt.Errorf("failed to check block %s version %s in the registry: %s, httpStatusCode: %v", name, version, respData.Error, resp.StatusCode)
}

const (
	hintRegistryUnreachable = "check that the registry is running and that --clay-registry is its URL"
	hintRegistryURL         = "check that --clay-registry is the base URL of a Clay registry, for example https://clay.example.com"
)

func (r *Registry) checkHost() error {
	if r.host == "" {
		return errors.New("no Clay registry URL given\nhint: pass --clay-registry <url>")
	}
	if u, err := url.Parse(r.host); err != nil || (u.Scheme != "http" && u.Scheme != "https") {
		return fmt.Errorf("--clay-registry must start with http:// or https://, got %s", r.host)
	}
	return nil
}

func unreachableError(host string, err error) error {
	return fmt.Errorf("cannot reach the Clay registry at %s: %w\nhint: %s", host, err, hintRegistryUnreachable)
}

func notARegistryError(url string, status int, err error) error {
	hint := hintRegistryURL
	if status >= http.StatusInternalServerError {
		hint = hintRegistryUnreachable
	}
	return fmt.Errorf("the response from %s is not from a Clay registry (HTTP %d): %w\nhint: %s", url, status, err, hint)
}
