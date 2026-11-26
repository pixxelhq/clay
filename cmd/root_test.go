package cmd

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func executeRoot(t *testing.T, args ...string) error {
	t.Helper()
	RootCmd.SetArgs(args)
	t.Cleanup(func() { RootCmd.SetArgs(nil) })
	return RootCmd.Execute()
}

func TestRoot_MissingArgumentPointsAtHelp(t *testing.T) {
	err := executeRoot(t, "block", "describe")

	require.Error(t, err)
	assert.Equal(t, "accepts 1 arg(s), received 0\nhint: run 'clay block describe --help' to see its arguments", err.Error())
}

func TestRoot_UnknownFlagPointsAtHelp(t *testing.T) {
	err := executeRoot(t, "dockerfile", "--bogus")

	require.Error(t, err)
	assert.Equal(t, "unknown flag: --bogus\nhint: run 'clay dockerfile --help' to see the flags", err.Error())
}
