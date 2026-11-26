package cmd

import (
	"net/http"
	"testing"

	"github.com/pixxelhq/clay/pkg/registry"
	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestDescribeBlockCmd_Metadata(t *testing.T) {
	cmd, _, err := RootCmd.Find([]string{"block", "describe"})
	require.NoError(t, err)

	assert.Equal(t, "describe <name>", cmd.Use)
	assert.NotNil(t, cmd.RunE)
	assert.NotNil(t, cmd.Args)
	regFlag := cmd.Flags().Lookup("clay-registry")
	require.NotNil(t, regFlag)
	assert.Contains(t, regFlag.Usage, "CLAY_REGISTRY_HOST")
	assert.NotContains(t, regFlag.Annotations, cobra.BashCompOneRequiredFlag)
	assert.NotNil(t, cmd.Flags().Lookup("version"))
	assert.NotNil(t, cmd.Flags().ShorthandLookup("v"))
}

func TestDescribeBlock_ArgValidation(t *testing.T) {
	tests := []struct {
		name         string
		args         []string
		wantContains []string
	}{
		{
			name:         "missing block name",
			args:         []string{"block", "describe"},
			wantContains: []string{"1 arg(s)", "received 0", "clay block describe --help"},
		},
		{
			name:         "too many positional args",
			args:         []string{"block", "describe", "a", "b"},
			wantContains: []string{"1 arg(s)", "received 2", "clay block describe --help"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			out, err := runViaRoot(t, tt.args...)

			require.Error(t, err)
			for _, sub := range tt.wantContains {
				assert.Contains(t, err.Error(), sub)
			}
			assert.Empty(t, out)
		})
	}
}

func TestDescribeBlock_QueriesAndFormatting(t *testing.T) {
	versions := registry.Blocks{
		{ID: "2", Name: "ndvi", Kind: "block", Type: "processing", Version: "0.2.0", DockerImage: "reg/ndvi:0.2.0"},
		{ID: "1", Name: "ndvi", Kind: "block", Type: "processing", Version: "0.1.0", DockerImage: "reg/ndvi:0.1.0"},
	}
	single := registry.Block{
		ID:          "2",
		Name:        "ndvi",
		Kind:        "block",
		Type:        "processing",
		Version:     "0.2.0",
		DockerImage: "reg/ndvi:0.2.0",
	}

	tests := []struct {
		name        string
		makeArgs    func(serverURL string) []string
		wantRequest string
		verifyOut   func(t *testing.T, out string)
	}{
		{
			name: "all versions when --version is omitted",
			makeArgs: func(serverURL string) []string {
				return []string{"block", "describe", "ndvi", "--clay-registry", serverURL}
			},
			wantRequest: "GET /v1/blocks/ndvi",
			verifyOut:   func(t *testing.T, out string) { assertIndentedJSON(t, out, "\n    \"id\"", versions) },
		},
		{
			name: "specific version via --version",
			makeArgs: func(serverURL string) []string {
				return []string{"block", "describe", "ndvi", "--clay-registry", serverURL, "--version", "0.2.0"}
			},
			wantRequest: "GET /v1/blocks/ndvi/versions/0.2.0",
			verifyOut:   func(t *testing.T, out string) { assertIndentedJSON(t, out, "\n  \"id\"", single) },
		},
		{
			name: "specific version via -v shorthand",
			makeArgs: func(serverURL string) []string {
				return []string{"block", "describe", "ndvi", "--clay-registry", serverURL, "-v", "0.2.0"}
			},
			wantRequest: "GET /v1/blocks/ndvi/versions/0.2.0",
			verifyOut:   func(t *testing.T, out string) { assertIndentedJSON(t, out, "\n  \"id\"", single) },
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rec, server := newBlockRegistryServer(t, func(w http.ResponseWriter, r *http.Request) {
				switch r.URL.Path {
				case "/v1/blocks/ndvi":
					respondJSON(t, w, http.StatusOK, registry.RegistryResponse[registry.Blocks]{Data: versions})
				case "/v1/blocks/ndvi/versions/0.2.0":
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

func TestDescribeBlock_RegistryHostEnvAndEdgeCases(t *testing.T) {
	single := registry.Block{ID: "2", Name: "ndvi", Version: "0.2.0", DockerImage: "reg/ndvi:0.2.0"}
	assertRegistryHostEnvBehavior(t, []string{"block", "describe", "ndvi", "--version", "0.2.0"}, "GET /v1/blocks/ndvi/versions/0.2.0", single)
}

func TestDescribeBlock_ServerErrorsPropagate(t *testing.T) {
	cases := []struct {
		name string
		args []string
	}{
		{name: "all versions", args: []string{"ndvi"}},
		{name: "specific version", args: []string{"ndvi", "--version", "0.2.0"}},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, server := newBlockRegistryServer(t, func(w http.ResponseWriter, _ *http.Request) {
				respondJSON(t, w, http.StatusNotFound, registry.RegistryResponse[any]{Error: "block not found"})
			})

			args := append([]string{"block", "describe"}, tc.args...)
			args = append(args, "--clay-registry", server.URL)
			out, err := runViaRoot(t, args...)

			require.Error(t, err)
			assert.Contains(t, err.Error(), "block not found")
			assert.Empty(t, out)
		})
	}
}
