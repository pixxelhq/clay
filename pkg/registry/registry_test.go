package registry

import (
	"net/http"
	"net/http/httptest"
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
                        "documentation_url": "url1",
                        "specification": null
                    }
                ],
                "error": ""
            }`,
			serverStatus: http.StatusOK,
			expectedBlocks: Blocks{
				&Block{
					ID:               "1",
					Name:             "block1",
					Kind:             "kind1",
					Type:             "type1",
					Version:          "v1",
					DockerImage:      "image1",
					DocumentationURL: "url1",
					Specification:    nil,
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
			expectedError:  "failed to unmarshall response for list blocks: invalid character '}' looking for beginning of value",
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

			// Create a blockRegistry instance with the test server URL
			br := NewBlockRegistry(server.URL, 2*time.Second)

			// Call the ListBlocks method
			blocks, err := br.ListBlocks()

			// Check the expected error
			if tt.expectedError != "" && err.Error() != tt.expectedError {
				t.Errorf("expected error: %v, got: %v", tt.expectedError, err)
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
		if *a[i] != *b[i] {
			return false
		}
	}
	return true
}
