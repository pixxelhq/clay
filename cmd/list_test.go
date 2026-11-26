package cmd

import (
	"net/http"
	"testing"

	"github.com/pixxelhq/clay/pkg/registry"
	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestListBlockRegistryCmd_Metadata(t *testing.T) {
	cmd, _, err := RootCmd.Find([]string{"block", "list"})
	require.NoError(t, err)

	assert.Equal(t, "list", cmd.Use)
	assert.NotNil(t, cmd.RunE)
	regFlag := cmd.Flags().Lookup("clay-registry")
	require.NotNil(t, regFlag)
	assert.Contains(t, regFlag.Usage, "CLAY_REGISTRY_HOST")
	assert.NotContains(t, regFlag.Annotations, cobra.BashCompOneRequiredFlag)
	assert.NotNil(t, cmd.Flags().Lookup("name"))
	assert.NotNil(t, cmd.Flags().ShorthandLookup("n"))
	assert.NotNil(t, cmd.Flags().Lookup("version"))
	assert.NotNil(t, cmd.Flags().ShorthandLookup("v"))
}

func TestListBlockRegistry_QueriesAndFormatting(t *testing.T) {
	allBlocks := registry.Blocks{
		{ID: "1", Name: "ndvi", Kind: "block", Type: "processing", Version: "0.2.0", DockerImage: "reg/ndvi:0.2.0"},
		{ID: "2", Name: "cloud-mask", Kind: "block", Type: "ml", Version: "1.0.0", DockerImage: "reg/cloud-mask:1.0.0"},
	}
	versions := registry.Blocks{
		{ID: "1", Name: "ndvi", Kind: "block", Type: "processing", Version: "0.2.0", DockerImage: "reg/ndvi:0.2.0"},
		{ID: "0", Name: "ndvi", Kind: "block", Type: "processing", Version: "0.1.0", DockerImage: "reg/ndvi:0.1.0"},
	}
	single := registry.Block{
		ID:          "0",
		Name:        "ndvi",
		Kind:        "block",
		Type:        "processing",
		Version:     "0.1.0",
		DockerImage: "reg/ndvi:0.1.0",
	}

	tests := []struct {
		name        string
		makeArgs    func(serverURL string) []string
		wantRequest string
		verifyOut   func(t *testing.T, out string)
	}{
		{
			name:        "all blocks with no filters",
			makeArgs:    func(serverURL string) []string { return []string{"block", "list", "--clay-registry", serverURL} },
			wantRequest: "GET /v1/blocks",
			verifyOut:   func(t *testing.T, out string) { assertIndentedJSON(t, out, "\n    \"id\"", allBlocks) },
		},
		{
			name: "filter by --name",
			makeArgs: func(serverURL string) []string {
				return []string{"block", "list", "--clay-registry", serverURL, "--name", "ndvi"}
			},
			wantRequest: "GET /v1/blocks/ndvi",
			verifyOut:   func(t *testing.T, out string) { assertIndentedJSON(t, out, "\n    \"id\"", versions) },
		},
		{
			name: "filter by -n and -v shorthands",
			makeArgs: func(serverURL string) []string {
				return []string{"block", "list", "--clay-registry", serverURL, "-n", "ndvi", "-v", "0.1.0"}
			},
			wantRequest: "GET /v1/blocks/ndvi/versions/0.1.0",
			verifyOut:   func(t *testing.T, out string) { assertIndentedJSON(t, out, "\n  \"id\"", single) },
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rec, server := newBlockRegistryServer(t, func(w http.ResponseWriter, r *http.Request) {
				switch r.URL.Path {
				case "/v1/blocks":
					respondJSON(t, w, http.StatusOK, registry.RegistryResponse[registry.Blocks]{Data: allBlocks})
				case "/v1/blocks/ndvi":
					respondJSON(t, w, http.StatusOK, registry.RegistryResponse[registry.Blocks]{Data: versions})
				case "/v1/blocks/ndvi/versions/0.1.0":
					respondJSON(t, w, http.StatusOK, registry.RegistryResponse[registry.Block]{Data: single})
				default:
					respondJSON(t, w, http.StatusNotFound, registry.RegistryResponse[any]{Error: "not found"})
				}
			})

			out, err := runViaRoot(t, tt.makeArgs(server.URL)...)

			require.NoError(t, err)
			assert.Equal(t, []string{tt.wantRequest}, rec.snapshot())
			tt.verifyOut(t, out)
		})
	}
}

func TestListBlockRegistry_RegistryHostEnvAndEdgeCases(t *testing.T) {
	expected := registry.Blocks{
		{ID: "1", Name: "ndvi", Version: "0.1.0", DockerImage: "reg/ndvi:0.1.0"},
	}
	assertRegistryHostEnvBehavior(t, []string{"block", "list"}, "GET /v1/blocks", expected)
}

func TestListBlockRegistry_ServerErrorsPropagate(t *testing.T) {
	cases := []struct {
		name string
		args []string
	}{
		{name: "list all blocks", args: nil},
		{name: "filter by name", args: []string{"-n", "ndvi"}},
		{name: "filter by name and version", args: []string{"-n", "ndvi", "-v", "0.1.0"}},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, server := newBlockRegistryServer(t, func(w http.ResponseWriter, _ *http.Request) {
				respondJSON(t, w, http.StatusInternalServerError, registry.RegistryResponse[any]{Error: "registry unavailable"})
			})

			args := append([]string{"block", "list", "--clay-registry", server.URL}, tc.args...)
			out, err := runViaRoot(t, args...)

			require.Error(t, err)
			assert.Contains(t, err.Error(), "registry unavailable")
			assert.Empty(t, out)
		})
	}
}
