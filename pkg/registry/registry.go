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
	host    string
	timeout time.Duration
}

func NewModelRegistry(host string, timeout time.Duration) *modelRegistry {
	return &modelRegistry{
		host:    host,
		timeout: timeout,
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

type PublishModelResponse struct {
	Data  any    `json:"data"`
	Error string `json:"error"`
}

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

	client := &http.Client{
		Timeout: mr.timeout,
	}
	resp, err := client.Do(httpReq)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if err = handlerHTTPStatusCode(resp); err != nil {
		return err
	}

	return nil
}

func handlerHTTPStatusCode(resp *http.Response) error {
	if resp.StatusCode == http.StatusCreated {
		return nil
	}

	if resp.StatusCode == http.StatusConflict {
		return ErrAlreadyExists
	}

	var respData PublishModelResponse
	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		return fmt.Errorf("failed to decode response: %w", err)
	}

	return fmt.Errorf("failed to create block, status code: %d: %s", resp.StatusCode, respData.Error)
}
