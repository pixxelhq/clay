package config

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func projectWithSpec(t *testing.T, spec string) string {
	t.Helper()
	dir := t.TempDir()
	require.NoError(t, os.WriteFile(filepath.Join(dir, "clay.yaml"), []byte(spec), 0644))
	return dir
}

func TestGetConfig_UnquotedPythonVersionSaysToQuoteIt(t *testing.T) {
	dir := projectWithSpec(t, "name: demo\nbuild:\n  python-version: 3.10\n")

	_, err := GetConfig(dir)

	require.Error(t, err)
	assert.Equal(t, "clay.yaml: build.python-version must be text, not a number\n"+
		"hint: put the value in quotes so that YAML reads it as text", err.Error())
}

func TestGetConfig_WrongTypeNamesFieldAndExpectedType(t *testing.T) {
	dir := projectWithSpec(t, "name: demo\ngpu: \"yes\"\n")

	_, err := GetConfig(dir)

	require.Error(t, err)
	assert.Equal(t, "clay.yaml: gpu must be true or false, not text\n"+
		"hint: see the clay.yaml reference: https://pixxelhq.github.io/clay/spec/", err.Error())
}

func TestGetConfig_InvalidYAML(t *testing.T) {
	dir := projectWithSpec(t, "name: demo\nbuild:\n  python-version: \"3.10\n")

	_, err := GetConfig(dir)

	require.Error(t, err)
	assert.Contains(t, err.Error(), "clay.yaml is not valid YAML: ")
	assert.Contains(t, err.Error(), "\nhint: check the indentation and quotes")
}

func TestGetConfig_MissingFile(t *testing.T) {
	_, err := GetConfig(t.TempDir())

	require.Error(t, err)
	assert.Contains(t, err.Error(), "no clay.yaml in ")
	assert.Contains(t, err.Error(), "\nhint: ")
}

func TestGetConfig_TopLevelNotAMapping(t *testing.T) {
	dir := projectWithSpec(t, "- just\n- a list\n")

	_, err := GetConfig(dir)

	require.Error(t, err)
	assert.Equal(t, "clay.yaml must be a mapping, not a list\n"+
		"hint: see the clay.yaml reference: https://pixxelhq.github.io/clay/spec/", err.Error())
}
