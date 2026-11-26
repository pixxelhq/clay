package cmd

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"

	"github.com/pixxelhq/clay/pkg/registry"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// recordedRegistryRequest stores the HTTP method and path received by a fake registry server.
type recordedRegistryRequest struct {
	mu       sync.Mutex
	requests []string
}

func (r *recordedRegistryRequest) snapshot() []string {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]string, len(r.requests))
	copy(out, r.requests)
	return out
}

func newBlockRegistryServer(t *testing.T, handler func(w http.ResponseWriter, r *http.Request)) (*recordedRegistryRequest, *httptest.Server) {
	t.Helper()
	rec := &recordedRegistryRequest{}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rec.mu.Lock()
		rec.requests = append(rec.requests, r.Method+" "+r.URL.Path)
		rec.mu.Unlock()
		handler(w, r)
	}))
	t.Cleanup(server.Close)
	return rec, server
}

func resetNamedFlags(t *testing.T, path []string, flagNames ...string) {
	t.Helper()
	cmd, _, err := RootCmd.Find(path)
	require.NoError(t, err)
	for _, flagName := range flagNames {
		f := cmd.Flags().Lookup(flagName)
		require.NotNil(t, f)
		require.NoError(t, f.Value.Set(f.DefValue))
		f.Changed = false
	}
}

func saveBlockFlags(t *testing.T) {
	t.Helper()
	origHost, origName, origVersion, origDescribeVersion := clayRegistryHost, name, version, describeCmdVersion
	t.Cleanup(func() {
		resetNamedFlags(t, []string{"block", "list"}, "clay-registry", "name", "version")
		resetNamedFlags(t, []string{"block", "describe"}, "clay-registry", "version")
		RootCmd.SetArgs(nil)
		clayRegistryHost = origHost
		name = origName
		version = origVersion
		describeCmdVersion = origDescribeVersion
	})
}

func runViaRoot(t *testing.T, args ...string) (string, error) {
	t.Helper()
	saveBlockFlags(t)
	RootCmd.SetArgs(args)

	var err error
	out := captureStdout(t, func() {
		err = RootCmd.Execute()
	})
	return out, err
}

func respondJSON(t *testing.T, w http.ResponseWriter, status int, payload any) {
	t.Helper()
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	assert.NoError(t, json.NewEncoder(w).Encode(payload))
}

func assertIndentedJSON[T any](t *testing.T, out, indentMarker string, want T) {
	t.Helper()
	assert.Contains(t, out, indentMarker)
	var got T
	require.NoError(t, json.Unmarshal([]byte(out), &got))
	assert.Equal(t, want, got)
}

func assertRegistryHostEnvBehavior[T any](t *testing.T, baseArgs []string, wantRequest string, wantPayload T) {
	t.Helper()

	t.Run("uses CLAY_REGISTRY_HOST when flag is omitted", func(t *testing.T) {
		rec, server := newBlockRegistryServer(t, func(w http.ResponseWriter, _ *http.Request) {
			respondJSON(t, w, http.StatusOK, registry.RegistryResponse[T]{Data: wantPayload})
		})
		t.Setenv("CLAY_REGISTRY_HOST", server.URL)

		out, err := runViaRoot(t, baseArgs...)

		require.NoError(t, err)
		assert.Equal(t, []string{wantRequest}, rec.snapshot())
		var got T
		require.NoError(t, json.Unmarshal([]byte(out), &got))
		assert.Equal(t, wantPayload, got)
	})

	t.Run("--clay-registry flag overrides CLAY_REGISTRY_HOST", func(t *testing.T) {
		rec, server := newBlockRegistryServer(t, func(w http.ResponseWriter, _ *http.Request) {
			respondJSON(t, w, http.StatusOK, registry.RegistryResponse[T]{Data: wantPayload})
		})
		t.Setenv("CLAY_REGISTRY_HOST", "http://127.0.0.1:1")

		args := append(append([]string{}, baseArgs...), "--clay-registry", server.URL)
		out, err := runViaRoot(t, args...)

		require.NoError(t, err)
		assert.Equal(t, []string{wantRequest}, rec.snapshot())
		var got T
		require.NoError(t, json.Unmarshal([]byte(out), &got))
		assert.Equal(t, wantPayload, got)
	})

	t.Run("explicit empty --clay-registry falls back to CLAY_REGISTRY_HOST like publish", func(t *testing.T) {
		rec, server := newBlockRegistryServer(t, func(w http.ResponseWriter, _ *http.Request) {
			respondJSON(t, w, http.StatusOK, registry.RegistryResponse[T]{Data: wantPayload})
		})
		t.Setenv("CLAY_REGISTRY_HOST", server.URL)

		args := append(append([]string{}, baseArgs...), "--clay-registry", "")
		out, err := runViaRoot(t, args...)

		require.NoError(t, err)
		assert.Equal(t, []string{wantRequest}, rec.snapshot())
		var got T
		require.NoError(t, json.Unmarshal([]byte(out), &got))
		assert.Equal(t, wantPayload, got)
	})

	t.Run("explicit empty --clay-registry without env returns missing-URL hint", func(t *testing.T) {
		t.Setenv("CLAY_REGISTRY_HOST", "")

		args := append(append([]string{}, baseArgs...), "--clay-registry", "")
		out, err := runViaRoot(t, args...)

		require.Error(t, err)
		assert.Equal(t, "no Clay registry URL given\nhint: pass --clay-registry <url> or set CLAY_REGISTRY_HOST", err.Error())
		assert.Empty(t, out)
	})

	t.Run("errors with hint when neither flag nor CLAY_REGISTRY_HOST is set", func(t *testing.T) {
		t.Setenv("CLAY_REGISTRY_HOST", "")

		out, err := runViaRoot(t, baseArgs...)

		require.Error(t, err)
		assert.Equal(t, "no Clay registry URL given\nhint: pass --clay-registry <url> or set CLAY_REGISTRY_HOST", err.Error())
		assert.Empty(t, out)
	})

	t.Run("whitespace-only CLAY_REGISTRY_HOST fails registry URL validation like publish", func(t *testing.T) {
		t.Setenv("CLAY_REGISTRY_HOST", "   ")

		out, err := runViaRoot(t, baseArgs...)

		require.Error(t, err)
		assert.NotContains(t, err.Error(), "no Clay registry URL given")
		assert.Contains(t, err.Error(), "http://")
		assert.Contains(t, err.Error(), "https://")
		assert.Empty(t, out)
	})
}

func TestBlockCmd_Subcommands(t *testing.T) {
	blockCmd, _, err := RootCmd.Find([]string{"block"})
	require.NoError(t, err)
	assert.Equal(t, "block <command>", blockCmd.Use)

	subNames := make([]string, 0, len(blockCmd.Commands()))
	for _, sub := range blockCmd.Commands() {
		subNames = append(subNames, sub.Name())
	}
	assert.Contains(t, subNames, "list")
	assert.Contains(t, subNames, "describe")
}

func TestWritePrettyJSON_ReturnsMarshalError(t *testing.T) {
	badBlock := &registry.Block{
		ID:            "1",
		Name:          "broken",
		Version:       "0.0.1",
		Specification: &registry.Specification{Inputs: json.RawMessage("{invalid")},
	}

	var err error
	out := captureStdout(t, func() {
		err = writePrettyJSON(badBlock)
	})

	require.Error(t, err)
	assert.Contains(t, err.Error(), "failed to generate pretty JSON")
	assert.Empty(t, out)
}
