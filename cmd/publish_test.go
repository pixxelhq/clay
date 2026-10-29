package cmd

import (
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"sync"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// fakeRegistry records the requests it receives and answers version lookups
// with versionStatus.
type fakeRegistry struct {
	mu       sync.Mutex
	requests []string
}

func newFakeRegistry(t *testing.T, versionStatus int) (*fakeRegistry, *httptest.Server) {
	t.Helper()
	fr := &fakeRegistry{}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fr.mu.Lock()
		fr.requests = append(fr.requests, r.Method+" "+r.URL.Path)
		fr.mu.Unlock()

		if r.Method == http.MethodGet {
			w.WriteHeader(versionStatus)
			body := `{"data":{}}`
			if versionStatus == http.StatusNotFound {
				body = `{"error":"block with the given name and version does not exists"}`
			}
			_, _ = w.Write([]byte(body))
			return
		}
		w.WriteHeader(http.StatusCreated)
	}))
	t.Cleanup(server.Close)
	return fr, server
}

// setupPublishProject creates a block project with a clay.yaml in a temp dir,
// makes it the working directory, and points the publish flags at registryURL.
// PATH is emptied so no docker command can run.
func setupPublishProject(t *testing.T, registryURL string) string {
	t.Helper()
	projectDir := t.TempDir()
	clayYAML := "name: myblock\nversion: 0.0.1\nbuild:\n  python_version: \"3.10\"\n"
	require.NoError(t, os.WriteFile(filepath.Join(projectDir, "clay.yaml"), []byte(clayYAML), 0644))

	wd, err := os.Getwd()
	require.NoError(t, err)
	require.NoError(t, os.Chdir(projectDir))
	t.Cleanup(func() { _ = os.Chdir(wd) })

	oldClay, oldDocker, oldDockerfile := clayRegistry, dockerRegistry, dockerfilePath
	clayRegistry, dockerRegistry, dockerfilePath = registryURL, "registry.example.com", ""
	t.Cleanup(func() { clayRegistry, dockerRegistry, dockerfilePath = oldClay, oldDocker, oldDockerfile })

	t.Setenv("PATH", t.TempDir())
	return projectDir
}

func TestPublish_ExistingVersionStopsBeforeBuild(t *testing.T) {
	fr, server := newFakeRegistry(t, http.StatusOK)
	projectDir := setupPublishProject(t, server.URL)

	err := publishBlockCmd(nil, nil)

	require.Error(t, err)
	assert.Contains(t, err.Error(), "myblock 0.0.1 is already published")
	assert.Contains(t, err.Error(), "hint: bump `version` in clay.yaml")
	assert.Equal(t, []string{"GET /v1/blocks/myblock/versions/0.0.1"}, fr.requests, "only the version lookup should reach the registry")
	_, statErr := os.Stat(filepath.Join(projectDir, "Dockerfile"))
	assert.True(t, os.IsNotExist(statErr), "build should not start, but a Dockerfile was generated")
}

func TestPublish_NewVersionGoesOnToBuild(t *testing.T) {
	fr, server := newFakeRegistry(t, http.StatusNotFound)
	projectDir := setupPublishProject(t, server.URL)

	err := publishBlockCmd(nil, nil)

	// The build itself fails because PATH is empty; what matters is that
	// publish got past the registry check and started the build.
	require.Error(t, err)
	assert.NotContains(t, err.Error(), "already published")
	assert.Equal(t, []string{"GET /v1/blocks/myblock/versions/0.0.1"}, fr.requests)
	_, statErr := os.Stat(filepath.Join(projectDir, "Dockerfile"))
	assert.NoError(t, statErr, "build should have started and generated a Dockerfile")
}

func TestPublish_RegistryErrorStopsBeforeBuild(t *testing.T) {
	_, server := newFakeRegistry(t, http.StatusInternalServerError)
	projectDir := setupPublishProject(t, server.URL)

	err := publishBlockCmd(nil, nil)

	require.Error(t, err)
	assert.Contains(t, err.Error(), "httpStatusCode: 500")
	_, statErr := os.Stat(filepath.Join(projectDir, "Dockerfile"))
	assert.True(t, os.IsNotExist(statErr), "build should not start when the registry check fails")
}
