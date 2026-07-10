package catalog

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gopkg.in/yaml.v3"
)

// writeFile creates name inside dir with the given contents.
func writeFile(t *testing.T, dir, name, contents string) {
	t.Helper()
	require.NoError(t, os.WriteFile(filepath.Join(dir, name), []byte(contents), 0644))
}

// fixtureProject copies the testdata catalog.yaml into a fresh temp dir
// alongside a stub clay.yaml, mimicking a real model repo root.
func fixtureProject(t *testing.T) string {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join("testdata", "catalog.yaml"))
	require.NoError(t, err)

	dir := t.TempDir()
	writeFile(t, dir, "clay.yaml", "name: waterqualityindexmodel\nversion: v0.15.23\n")
	writeFile(t, dir, catalogFileName, string(raw))
	return dir
}

// Present path: catalog.yaml next to clay.yaml is discovered and read; media
// lands in the typed field, every other section in Sections.
func TestLoad_Present(t *testing.T) {
	dir := fixtureProject(t)

	c, err := Load(dir)
	require.NoError(t, err)
	require.NotNil(t, c)

	assert.Equal(t, "catalog_readme/thumbnail.png", c.Media["thumbnail"])
	for _, key := range []string{"description", "input_data", "output_data", "technical_details"} {
		assert.Contains(t, c.Sections, key, "opaque section %q missing from Sections", key)
	}
	assert.NotContains(t, c.Sections, "media", "media must not leak into Sections")
}

// Round-trip: Load then Bytes yields YAML with the same content (formatting
// and comments are not preserved — the catalog is data, not a document).
func TestBytes_RoundTripContent(t *testing.T) {
	dir := fixtureProject(t)
	c, err := Load(dir)
	require.NoError(t, err)

	out, err := c.Bytes()
	require.NoError(t, err)

	reloaded := &Catalog{}
	require.NoError(t, yaml.Unmarshal(out, reloaded))
	assert.Equal(t, c.Media, reloaded.Media)
	assert.Equal(t, c.Sections, reloaded.Sections)
}

// JSON merges media and the opaque sections into a single document.
func TestJSON_StructuredContent(t *testing.T) {
	dir := fixtureProject(t)
	c, err := Load(dir)
	require.NoError(t, err)

	out, err := c.JSON()
	require.NoError(t, err)

	var doc map[string]interface{}
	require.NoError(t, json.Unmarshal(out, &doc))

	for _, key := range []string{"media", "description", "input_data", "output_data", "technical_details"} {
		assert.Contains(t, doc, key, "catalog JSON missing %q", key)
	}
	media, ok := doc["media"].(map[string]interface{})
	require.True(t, ok)
	assert.Equal(t, "catalog_readme/thumbnail.png", media["thumbnail"])
}

// Rewriting media is a plain map assignment; Bytes and JSON reflect it.
func TestMediaRewrite_ReflectedInOutputs(t *testing.T) {
	dir := fixtureProject(t)
	c, err := Load(dir)
	require.NoError(t, err)

	url := "https://b.s3.us-east-1.amazonaws.com/m/v1/catalog_readme/thumbnail.png"
	c.Media["thumbnail"] = url

	out, err := c.Bytes()
	require.NoError(t, err)
	reloaded := &Catalog{}
	require.NoError(t, yaml.Unmarshal(out, reloaded))
	assert.Equal(t, url, reloaded.Media["thumbnail"])

	jsonOut, err := c.JSON()
	require.NoError(t, err)
	var doc map[string]interface{}
	require.NoError(t, json.Unmarshal(jsonOut, &doc))
	assert.Equal(t, url, doc["media"].(map[string]interface{})["thumbnail"])
}

// Absent path: a project with no catalog.yaml yields (nil, nil) so publish is non-breaking.
func TestLoad_Absent(t *testing.T) {
	dir := t.TempDir()
	writeFile(t, dir, "clay.yaml", "name: somemodel\n")

	c, err := Load(dir)
	require.NoError(t, err)
	assert.Nil(t, c)
}

// Malformed path: a syntactically invalid catalog.yaml fails loudly.
func TestLoad_Malformed(t *testing.T) {
	dir := t.TempDir()
	writeFile(t, dir, catalogFileName, "media: [unterminated\n  : : :\n")

	c, err := Load(dir)
	require.Error(t, err)
	assert.Nil(t, c)
}

// Typed media map rejects non-string values at parse time.
func TestLoad_NonStringMediaValue(t *testing.T) {
	dir := t.TempDir()
	writeFile(t, dir, catalogFileName, "media:\n  thumbnail:\n    - not\n    - a-string\n")

	c, err := Load(dir)
	require.Error(t, err)
	assert.Nil(t, c)
}
