package registry

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"
	"time"
)

func TestListBlocks(t *testing.T) {
	tests := []struct {
		name           string
		serverResponse string
		serverStatus   int
		expectedBlocks Blocks
		expectedError  string
	}{
		{
			name: "successful response",
			serverResponse: `{
                "data": [
                    {
                        "id": "1",
                        "name": "block1",
                        "kind": "kind1",
                        "type": "type1",
                        "version": "v1",
                        "docker_image": "image1",
                        "specification": null
                    }
                ],
                "error": ""
            }`,
			serverStatus: http.StatusOK,
			expectedBlocks: Blocks{
				&Block{
					ID:            "1",
					Name:          "block1",
					Kind:          "kind1",
					Type:          "type1",
					Version:       "v1",
					DockerImage:   "image1",
					Specification: nil,
				},
			},
			expectedError: "",
		},
		{
			name:           "server error response",
			serverResponse: `{"data": null, "error": "internal server error"}`,
			serverStatus:   http.StatusInternalServerError,
			expectedBlocks: nil,
			expectedError:  "failed to list blocks: internal server error",
		},
		{
			name:           "invalid JSON response",
			serverResponse: `{"data": [}`,
			serverStatus:   http.StatusInternalServerError,
			expectedBlocks: nil,
			expectedError:  "the response from {{host}}/v1/blocks is not from a Clay registry: invalid character '}' looking for beginning of value\nhint: " + hintRegistryURL,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a test server
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(tt.serverStatus)
				w.Write([]byte(tt.serverResponse))
			}))
			defer server.Close()

			// Create a Registry instance with the test server URL
			r := New(server.URL, 2*time.Second)

			// Call the ListBlocks method
			blocks, err := r.ListBlocks()

			// Check the expected error
			wantErr := strings.ReplaceAll(tt.expectedError, "{{host}}", server.URL)
			if tt.expectedError != "" && err.Error() != wantErr {
				t.Errorf("expected error: %v, got: %v", wantErr, err)
			}

			// Check the expected blocks
			if !compareBlocks(blocks, tt.expectedBlocks) {
				t.Errorf("expected blocks: %v, got: %v", tt.expectedBlocks, blocks)
			}
		})
	}
}

// Helper function to compare two blocks slices
func compareBlocks(a, b Blocks) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if !reflect.DeepEqual(*a[i], *b[i]) {
			return false
		}
	}
	return true
}

func TestPublishBlockRequest_CatalogURLOmitEmpty(t *testing.T) {
	// Without a catalog URL, the field must be absent so existing publish flows
	// (and the registry client) see the same shape as before.
	without, err := json.Marshal(&PublishBlockRequest{Name: "m", Version: "v1"})
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(without), "catalog") {
		t.Errorf("catalog_url should be omitted when empty: %s", without)
	}

	// With a catalog URL, it is carried under "catalog_url".
	with, err := json.Marshal(&PublishBlockRequest{
		Name:       "m",
		Version:    "v1",
		CatalogURL: "https://x/catalog.yaml",
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(with), `"catalog_url":"https://x/catalog.yaml"`) {
		t.Errorf("catalog_url should be set: %s", with)
	}
}

func TestVersionExists(t *testing.T) {
	tests := []struct {
		name          string
		serverStatus  int
		serverBody    string
		expected      bool
		expectedError string
	}{
		{name: "version exists", serverStatus: http.StatusOK, serverBody: `{"data":{}}`, expected: true},
		{name: "version does not exist", serverStatus: http.StatusNotFound, serverBody: `{"error":"block with the given name and version does not exists"}`, expected: false},
		{
			name:          "404 from a non-registry route",
			serverStatus:  http.StatusNotFound,
			serverBody:    "404 page not found",
			expectedError: "the response from {{host}}/v1/blocks/myblock/versions/0.0.1 is not from a Clay registry: HTTP 404 without a registry error\nhint: " + hintRegistryURL,
		},
		{
			name:          "registry error",
			serverStatus:  http.StatusInternalServerError,
			serverBody:    `{"error":"something went wrong"}`,
			expectedError: "failed to check block myblock version 0.0.1 in the registry: something went wrong, httpStatusCode: 500",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var gotPath string
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				gotPath = r.Method + " " + r.URL.Path
				w.WriteHeader(tt.serverStatus)
				w.Write([]byte(tt.serverBody))
			}))
			defer server.Close()

			exists, err := New(server.URL, 2*time.Second).VersionExists("myblock", "0.0.1")

			if gotPath != "GET /v1/blocks/myblock/versions/0.0.1" {
				t.Errorf("unexpected request: %s", gotPath)
			}
			if tt.expectedError != "" {
				wantErr := strings.ReplaceAll(tt.expectedError, "{{host}}", server.URL)
				if err == nil || err.Error() != wantErr {
					t.Fatalf("expected error: %v, got: %v", wantErr, err)
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if exists != tt.expected {
				t.Errorf("expected exists=%v, got %v", tt.expected, exists)
			}
		})
	}
}

func TestRegistry_UnreachableSaysToCheckRegistry(t *testing.T) {
	server := httptest.NewServer(http.NotFoundHandler())
	host := server.URL
	server.Close()

	_, err := New(host, 2*time.Second).ListBlocks()

	if err == nil {
		t.Fatal("expected an error")
	}
	if !strings.HasPrefix(err.Error(), "cannot reach the Clay registry at "+host+": ") ||
		!strings.HasSuffix(err.Error(), "\nhint: "+hintRegistryUnreachable) {
		t.Errorf("unexpected error: %v", err)
	}
}

func TestRegistry_NoURLSaysToPassIt(t *testing.T) {
	_, err := New("", 2*time.Second).ListBlocks()

	if err == nil || err.Error() != "no Clay registry URL given\nhint: pass --clay-registry <url>" {
		t.Errorf("unexpected error: %v", err)
	}
}
