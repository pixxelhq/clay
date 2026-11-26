package cmd

import (
	"encoding/json"
	"testing"

	"github.com/pixxelhq/clay/pkg/registry"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

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
