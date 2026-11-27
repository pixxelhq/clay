package config

import (
	"os"
	"path/filepath"
	"strings"
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
	spec := strings.Replace(validV1Spec, `python-version: "3.10"`, "python-version: 3.10", 1)

	_, err := GetConfig(projectWithSpec(t, spec))

	require.Error(t, err)
	assert.Contains(t, err.Error(), "clay.yaml: build.python-version: must be text, not a number; "+
		"put the value in quotes so that YAML reads it as text")
}

func TestGetConfig_WrongTypeNamesFieldAndExpectedType(t *testing.T) {
	_, err := GetConfig(projectWithSpec(t, validV1Spec+"gpu: \"yes\"\n"))

	require.Error(t, err)
	assert.Contains(t, err.Error(), "clay.yaml: gpu: got string, want boolean")
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

const validV1Spec = `apiVersion: clay/v1
kind: block
type: processing
name: demo
version: 1.2.3
author: someone
inputs:
  - name: aoi
    format: vector
    type: url
    validation:
      min_area: 10
outputs: []
build:
  python-version: "3.10"
  requirements: requirements.txt
`

func TestGetConfig_V1Valid(t *testing.T) {
	cfg, err := GetConfig(projectWithSpec(t, validV1Spec))

	require.NoError(t, err)
	assert.Equal(t, "clay/v1", cfg.APIVersion)
	assert.Equal(t, "1.2.3", cfg.Version)
	assert.Equal(t, "3.10", cfg.Bulid.PythonVersion)
}

func TestGetConfig_V1UnknownTopLevelKey(t *testing.T) {
	_, err := GetConfig(projectWithSpec(t, validV1Spec+"title: Demo\n"))

	require.Error(t, err)
	assert.Equal(t, "clay.yaml does not match the clay/v1 schema:\n"+
		"  clay.yaml: additional properties 'title' not allowed\n"+
		"hint: see the clay.yaml reference: https://pixxelhq.github.io/clay/spec/", err.Error())
}

func TestGetConfig_V1UnknownInputKeyNamesTheInput(t *testing.T) {
	spec := strings.Replace(validV1Spec, "    type: url\n", "    type: url\n    formats: raster\n", 1)

	_, err := GetConfig(projectWithSpec(t, spec))

	require.Error(t, err)
	assert.Contains(t, err.Error(), "clay.yaml: inputs[0]: additional properties 'formats' not allowed")
}

func TestGetConfig_V1ValidationKeysDependOnFormat(t *testing.T) {
	spec := strings.Replace(validV1Spec, "min_area: 10", "min_value: 10", 1)

	_, err := GetConfig(projectWithSpec(t, spec))

	require.Error(t, err)
	assert.Contains(t, err.Error(), "clay.yaml: inputs[0].validation: additional properties 'min_value' not allowed")
}

func TestGetConfig_V1RejectsVersionWithV(t *testing.T) {
	spec := strings.Replace(validV1Spec, "version: 1.2.3", "version: v1.2.3", 1)

	_, err := GetConfig(projectWithSpec(t, spec))

	require.Error(t, err)
	assert.Contains(t, err.Error(), "clay.yaml: version: must be a semantic version without a leading v, such as 1.2.3")
}

func TestGetConfig_V1ReportsEveryProblem(t *testing.T) {
	spec := strings.Replace(validV1Spec, "author: someone\n", "", 1)
	spec = strings.Replace(spec, `python-version: "3.10"`, `python-version: "3.9"`, 1)

	_, err := GetConfig(projectWithSpec(t, spec))

	require.Error(t, err)
	assert.Contains(t, err.Error(), "clay.yaml: missing property 'author'")
	assert.Contains(t, err.Error(), "clay.yaml: build.python-version: ")
}

func TestGetConfig_MissingAPIVersion(t *testing.T) {
	spec := strings.Replace(validV1Spec, "apiVersion: clay/v1\n", "", 1)

	_, err := GetConfig(projectWithSpec(t, spec))

	require.Error(t, err)
	assert.Equal(t, "clay.yaml has no apiVersion\n"+
		"hint: add apiVersion: clay/v1, see https://pixxelhq.github.io/clay/spec/#moving-to-clayv1", err.Error())
}

func TestGetConfig_UnsupportedAPIVersion(t *testing.T) {
	spec := strings.Replace(validV1Spec, "apiVersion: clay/v1", "apiVersion: 0.0.1", 1)

	_, err := GetConfig(projectWithSpec(t, spec))

	require.Error(t, err)
	assert.Equal(t, "clay.yaml: apiVersion \"0.0.1\" is not supported by this version of Clay; supported: clay/v1\n"+
		"hint: to move an older clay.yaml to clay/v1, see https://pixxelhq.github.io/clay/spec/#moving-to-clayv1; "+
		"for a newer apiVersion, upgrade Clay", err.Error())
}

func TestSchemaV1_PublishedCopyMatches(t *testing.T) {
	published, err := os.ReadFile("../../mkdocs/docs/schema/v1.json")

	require.NoError(t, err)
	assert.Equal(t, string(schemaV1JSON), string(published), "copy pkg/config/schema/v1.json to mkdocs/docs/schema/v1.json")
}

func TestSchemaV1_ExamplesMatch(t *testing.T) {
	specs, err := filepath.Glob("../../examples/*/clay.yaml")
	require.NoError(t, err)
	require.NotEmpty(t, specs)

	for _, spec := range specs {
		cfg, err := GetConfig(filepath.Dir(spec))
		require.NoError(t, err, spec)
		assert.Equal(t, "clay/v1", cfg.APIVersion, spec)
	}
}
