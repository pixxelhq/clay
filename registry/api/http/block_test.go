package http

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/example/clay/registry/pkg/block"
	mock_block "github.com/example/clay/registry/pkg/block/mock"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"go.uber.org/mock/gomock"
)

func TestCreate(t *testing.T) {
	var blocks = getBlocks()
	testCases := []struct {
		name          string
		body          gin.H
		setupMocks    func(s *mock_block.MockService)
		checkResponse func(t *testing.T, recorder *httptest.ResponseRecorder)
	}{
		{
			name: "should return 2xx for valid request",
			body: gin.H{
				"id":                "uuid1_string_value",
				"name":              "Test Block",
				"kind":              "block",
				"type":              "processing",
				"version":           "1.0.0",
				"documentation_url": "http://example.com",
				"docker_image":      "example/image:latest",
				"specification": gin.H{
					"apiVersion":  "1.0.0",
					"title":       "Test Specification",
					"description": "This is a test specification",
					"author":      "Author Name",
					"parameters":  gin.H{},
					"inputs": gin.H{
						"key": "value",
					},
					"outputs": gin.H{
						"key": "value",
					},
					"build": gin.H{},
					"gpu":   true,
				},
			},
			setupMocks: func(s *mock_block.MockService) {
				s.EXPECT().Create(gomock.Any(), gomock.Any()).Times(1).Return(blocks[0], nil)
			},
			checkResponse: func(t *testing.T, recorder *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusCreated, recorder.Code)
				data, err := io.ReadAll(recorder.Body)
				assert.NoError(t, err)

				resp := &RegistryResponse[CreateBlockRequest]{}
				err = json.Unmarshal(data, &resp)
				assert.NoError(t, err)
				assert.Equal(t, "", resp.Error)

				assert.Equal(t, "Test Block", resp.Data.Name)
				assert.Equal(t, "1.0.0", resp.Data.Version)
				assert.Equal(t, true, resp.Data.Specification.GPU)
			},
		},
		{
			name: "should return 400 for bad request",
			body: gin.H{
				"name": "Test Block",
			},
			setupMocks: func(s *mock_block.MockService) {

			},
			checkResponse: func(t *testing.T, recorder *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusBadRequest, recorder.Code)
				data, err := io.ReadAll(recorder.Body)
				assert.NoError(t, err)

				resp := &RegistryResponse[CreateBlockRequest]{}
				err = json.Unmarshal(data, &resp)
				assert.NoError(t, err)
				assert.Equal(t, "code: BAD REQUEST, err: name, version, docker_image and documentation_url can not be empty", resp.Error)

			},
		},
	}

	for i := range testCases {
		tc := testCases[i]
		t.Run(tc.name, func(t *testing.T) {
			ctlr := gomock.NewController(t)
			defer ctlr.Finish()

			//route mapping with mocked block
			block := mock_block.NewMockService(ctlr)
			svr := NewServer()
			svr.LoadConfig()
			svr.Block = block
			svr.MapRoutes()

			data, err := json.Marshal(tc.body)
			require.NoError(t, err)

			//build request
			url := "/v1/blocks"
			req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(data))
			require.NoError(t, err)

			tc.setupMocks(block)

			recorder := httptest.NewRecorder()
			svr.Router.ServeHTTP(recorder, req)

			tc.checkResponse(t, recorder)

		})
	}
}

func TestGetBlocksWithLatestVersion(t *testing.T) {
	var blocks = getBlocks()
	testCases := []struct {
		name          string
		setupMocks    func(s *mock_block.MockService)
		checkResponse func(t *testing.T, recorder *httptest.ResponseRecorder)
	}{
		{
			name: "should return 200 and blocks for valid request",
			setupMocks: func(s *mock_block.MockService) {
				s.EXPECT().GetBlocksWithLatestVersion(gomock.Any()).Times(1).Return(blocks, nil)
			},
			checkResponse: func(t *testing.T, recorder *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusOK, recorder.Code)
				data, err := io.ReadAll(recorder.Body)
				assert.NoError(t, err)

				resp := &RegistryResponse[[]*GetLatestBlock]{}
				err = json.Unmarshal(data, &resp)
				assert.NoError(t, err)
				assert.Equal(t, "", resp.Error)
				assert.Len(t, resp.Data, 3)
			},
		},
		{
			name: "should return 500 for service error",
			setupMocks: func(s *mock_block.MockService) {
				s.EXPECT().GetBlocksWithLatestVersion(gomock.Any()).Times(1).Return(nil, assert.AnError)
			},
			checkResponse: func(t *testing.T, recorder *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusInternalServerError, recorder.Code)
				data, err := io.ReadAll(recorder.Body)
				assert.NoError(t, err)

				resp := &RegistryResponse[[]*block.Block]{}
				err = json.Unmarshal(data, &resp)
				assert.NoError(t, err)
				assert.Equal(t, "something went wrong", resp.Error)
			},
		},
	}

	for i := range testCases {
		tc := testCases[i]
		t.Run(tc.name, func(t *testing.T) {
			ctlr := gomock.NewController(t)
			defer ctlr.Finish()

			// route mapping with mocked block
			block := mock_block.NewMockService(ctlr)
			svr := NewServer()
			svr.LoadConfig()
			svr.Block = block
			svr.MapRoutes()

			tc.setupMocks(block)

			// build request
			url := "/v1/blocks"
			req, err := http.NewRequest(http.MethodGet, url, nil)
			require.NoError(t, err)

			recorder := httptest.NewRecorder()
			svr.Router.ServeHTTP(recorder, req)

			tc.checkResponse(t, recorder)
		})
	}
}

func TestGetBlockByName(t *testing.T) {
	var blocks = getBlocks()
	testCases := []struct {
		name          string
		blockName     string
		setupMocks    func(s *mock_block.MockService)
		checkResponse func(t *testing.T, recorder *httptest.ResponseRecorder)
	}{
		{
			name:      "should return 200 and block for valid request",
			blockName: "Test Block",
			setupMocks: func(s *mock_block.MockService) {
				s.EXPECT().GetBlockByName(gomock.Any(), "Test Block").Times(1).Return(blocks[:1], nil)
			},
			checkResponse: func(t *testing.T, recorder *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusOK, recorder.Code)
				data, err := io.ReadAll(recorder.Body)
				assert.NoError(t, err)

				resp := &RegistryResponse[[]*block.Block]{}
				err = json.Unmarshal(data, &resp)
				assert.NoError(t, err)
				assert.Equal(t, "", resp.Error)
				assert.Len(t, resp.Data, 1)
				assert.Equal(t, "Test Block", resp.Data[0].Name)
			},
		},
		{
			name:      "should return 500 for service error",
			blockName: "Test Block",
			setupMocks: func(s *mock_block.MockService) {
				s.EXPECT().GetBlockByName(gomock.Any(), "Test Block").Times(1).Return(nil, assert.AnError)
			},
			checkResponse: func(t *testing.T, recorder *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusInternalServerError, recorder.Code)
				data, err := io.ReadAll(recorder.Body)
				assert.NoError(t, err)

				resp := &RegistryResponse[[]*block.Block]{}
				err = json.Unmarshal(data, &resp)
				assert.NoError(t, err)
				assert.Equal(t, "something went wrong", resp.Error)
			},
		},
	}

	for i := range testCases {
		tc := testCases[i]
		t.Run(tc.name, func(t *testing.T) {
			ctlr := gomock.NewController(t)
			defer ctlr.Finish()

			// route mapping with mocked block
			block := mock_block.NewMockService(ctlr)
			svr := NewServer()
			svr.LoadConfig()
			svr.Block = block
			svr.MapRoutes()

			tc.setupMocks(block)

			// build request
			url := "/v1/blocks/" + tc.blockName
			req, err := http.NewRequest(http.MethodGet, url, nil)
			require.NoError(t, err)

			recorder := httptest.NewRecorder()
			svr.Router.ServeHTTP(recorder, req)

			tc.checkResponse(t, recorder)
		})
	}
}

func TestGetBlockByNameAndVersion(t *testing.T) {
	var blocks = getBlocks()
	testCases := []struct {
		name          string
		blockName     string
		blockVersion  string
		setupMocks    func(s *mock_block.MockService)
		checkResponse func(t *testing.T, recorder *httptest.ResponseRecorder)
	}{
		{
			name:         "should return 200 and block for valid request",
			blockName:    "Test Block",
			blockVersion: "1.0.0",
			setupMocks: func(s *mock_block.MockService) {
				s.EXPECT().GetBlockByNameAndVersion(gomock.Any(), "Test Block", "1.0.0").
					Times(1).
					Return(blocks[0], nil)
			},
			checkResponse: func(t *testing.T, recorder *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusOK, recorder.Code)
				data, err := io.ReadAll(recorder.Body)
				assert.NoError(t, err)

				resp := &RegistryResponse[*GetBlockByNameAndVersion]{}
				err = json.Unmarshal(data, &resp)
				assert.NoError(t, err)
				assert.Equal(t, "", resp.Error)
				assert.Equal(t, "Test Block", resp.Data.Name)
			},
		},
		{
			name:         "should return 500 for service error",
			blockName:    "Test Block",
			blockVersion: "1.0.0",
			setupMocks: func(s *mock_block.MockService) {
				s.EXPECT().GetBlockByNameAndVersion(gomock.Any(), "Test Block", "1.0.0").Times(1).Return(nil, assert.AnError)
			},
			checkResponse: func(t *testing.T, recorder *httptest.ResponseRecorder) {
				assert.Equal(t, http.StatusInternalServerError, recorder.Code)
				data, err := io.ReadAll(recorder.Body)
				assert.NoError(t, err)

				resp := &RegistryResponse[*block.Block]{}
				err = json.Unmarshal(data, &resp)
				assert.NoError(t, err)
				assert.Equal(t, "something went wrong", resp.Error)
			},
		},
	}

	for i := range testCases {
		tc := testCases[i]
		t.Run(tc.name, func(t *testing.T) {
			ctlr := gomock.NewController(t)
			defer ctlr.Finish()

			block := mock_block.NewMockService(ctlr)
			svr := NewServer()
			svr.LoadConfig()
			svr.Block = block
			svr.MapRoutes()

			tc.setupMocks(block)

			url := "/v1/blocks/" + tc.blockName + "/versions/" + tc.blockVersion
			req, err := http.NewRequest(http.MethodGet, url, nil)
			require.NoError(t, err)

			recorder := httptest.NewRecorder()
			svr.Router.ServeHTTP(recorder, req)

			tc.checkResponse(t, recorder)
		})
	}
}

func getBlocks() []*block.Block {
	uuid1 := uuid.New()
	uuid2 := uuid.New()
	return []*block.Block{
		{
			ID:               uuid1.String(),
			Name:             "Test Block",
			Kind:             "block",
			Type:             "processing",
			Version:          "1.0.0",
			DocumentationURL: "http://example.com",
			DockerImage:      "example/image:latest",
			Specification: &block.Specification{
				Version:     "1.0.0",
				Title:       "Test Specification",
				Description: "This is a test specification",
				Author:      "Author Name",
				Tags:        []string{"tag1", "tag2"},
				Parameters:  json.RawMessage(`{}`),
				Inputs:      json.RawMessage(`{"key": "value"}`),
				Outputs:     json.RawMessage(`{"key": "value"}`),
				Build:       json.RawMessage(`{}`),
				GPU:         true,
			},
		},
		{
			ID:               uuid1.String(),
			Name:             "Test Block",
			Kind:             "block",
			Type:             "processing",
			Version:          "1.1.0",
			DocumentationURL: "http://example.com",
			DockerImage:      "example/image:latest",
			Specification: &block.Specification{
				Version:     "1.0.0",
				Title:       "Test Specification",
				Description: "This is a test specification",
				Author:      "Author Name",
				Tags:        []string{"tag1", "tag2"},
				Parameters:  json.RawMessage(`{}`),
				Inputs:      json.RawMessage(`{"key": "value"}`),
				Outputs:     json.RawMessage(`{"key": "value"}`),
				Build:       json.RawMessage(`{}`),
			},
		},
		{
			ID:               uuid2.String(),
			Name:             "Test Block 2",
			Kind:             "block",
			Type:             "processing",
			Version:          "1.0.0",
			DocumentationURL: "http://example.com",
			DockerImage:      "example/image:latest",
			Specification: &block.Specification{
				Version:     "1.0.0",
				Title:       "Test Specification",
				Description: "This is a test specification",
				Author:      "Author Name",
				Tags:        []string{"tag1", "tag2"},
				Parameters:  json.RawMessage(`{}`),
				Inputs:      json.RawMessage(`{"key": "value"}`),
				Outputs:     json.RawMessage(`{"key": "value"}`),
				Build:       json.RawMessage(`{}`),
			},
		},
	}
}
