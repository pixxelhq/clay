package cmd

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/pixxelhq/clay-framework/pkg/catalog"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// fakeProvider records uploads instead of talking to S3.
type fakeProvider struct {
	uploaded map[string]string // remoteKey -> localPath
}

func (f *fakeProvider) Upload(ctx context.Context, localPath, remotePath string) error {
	f.uploaded[remotePath] = localPath
	return nil
}
func (f *fakeProvider) UploadDirectory(ctx context.Context, localDir, remotePrefix string) error {
	return nil
}
func (f *fakeProvider) Download(ctx context.Context, remotePath, localPath string) error {
	return nil
}
func (f *fakeProvider) List(ctx context.Context, prefix string) ([]string, error) { return nil, nil }
func (f *fakeProvider) Exists(ctx context.Context, remotePath string) (bool, error) {
	return false, nil
}

// catalogRepo writes a model repo with a catalog.yaml and the given media files.
func catalogRepo(t *testing.T, body string, files []string) string {
	t.Helper()
	dir := t.TempDir()
	for _, f := range files {
		p := filepath.Join(dir, f)
		require.NoError(t, os.MkdirAll(filepath.Dir(p), 0755))
		require.NoError(t, os.WriteFile(p, []byte("x"), 0644))
	}
	require.NoError(t, os.WriteFile(filepath.Join(dir, "catalog.yaml"), []byte(body), 0644))
	return dir
}

const testCatalogBody = `media:
  thumbnail: catalog_readme/thumbnail.png
  sample_input: catalog_readme/sample_input.jpg
  sample_output: catalog_readme/sample_output.jpg
description:
  - type: text
    body: hi
`

var testMediaFiles = []string{
	"catalog_readme/thumbnail.png",
	"catalog_readme/sample_input.jpg",
	"catalog_readme/sample_output.jpg",
}

// saveFlags snapshots the package-level flag globals and restores them after
// the test.
func saveFlags(t *testing.T) {
	t.Helper()
	origCatalog, origOut, origURL := catalogFile, catalogOut, storageURL
	t.Cleanup(func() { catalogFile, catalogOut, storageURL = origCatalog, origOut, origURL })
}

func TestRunCatalogUpload(t *testing.T) {
	saveFlags(t)
	dir := catalogRepo(t, testCatalogBody, testMediaFiles)

	catalogFile = "catalog.yaml"
	catalogOut = ""
	storageURL = "https://bkt.s3.us-east-1.amazonaws.com/my-block/v1/"

	fake := &fakeProvider{uploaded: map[string]string{}}
	// remotePrefix is what ProviderFromURL would strip from the URL path.
	require.NoError(t, runCatalogUpload(context.Background(), fake, "my-block/v1", dir))

	// Each media file was uploaded under <prefix>/<relPath>.
	require.Len(t, fake.uploaded, 3)
	assert.Contains(t, fake.uploaded, "my-block/v1/catalog_readme/thumbnail.png")
	assert.Contains(t, fake.uploaded, "my-block/v1/catalog_readme/sample_input.jpg")
	assert.Equal(t, filepath.Join(dir, "catalog_readme/thumbnail.png"), fake.uploaded["my-block/v1/catalog_readme/thumbnail.png"])

	// catalog.yaml was rewritten in place: media values are now full URLs and
	// the opaque sections survive.
	rewritten, err := catalog.LoadFile(filepath.Join(dir, "catalog.yaml"))
	require.NoError(t, err)
	require.NotNil(t, rewritten)

	assert.Equal(t, "https://bkt.s3.us-east-1.amazonaws.com/my-block/v1/catalog_readme/thumbnail.png", rewritten.Media["thumbnail"])
	assert.Equal(t, "https://bkt.s3.us-east-1.amazonaws.com/my-block/v1/catalog_readme/sample_input.jpg", rewritten.Media["sample_input"])

	desc := rewritten.Sections["description"].([]interface{})
	require.Len(t, desc, 1)
	assert.Equal(t, "hi", desc[0].(map[string]interface{})["body"])
}

// A missing declared file fails before anything is uploaded.
func TestRunCatalogUpload_MissingFileUploadsNothing(t *testing.T) {
	saveFlags(t)
	// Only two of the three declared files exist.
	dir := catalogRepo(t, testCatalogBody, testMediaFiles[:2])

	catalogFile = "catalog.yaml"
	storageURL = "https://bkt.s3.us-east-1.amazonaws.com/my-block/v1/"

	fake := &fakeProvider{uploaded: map[string]string{}}
	err := runCatalogUpload(context.Background(), fake, "my-block/v1", dir)
	require.Error(t, err)
	assert.Contains(t, err.Error(), "does not exist")
	assert.Empty(t, fake.uploaded, "no uploads should happen when validation fails")
}

func TestRunCatalogUpload_EmptyMedia(t *testing.T) {
	saveFlags(t)
	dir := catalogRepo(t, "description:\n  - type: text\n    body: hi\n", nil)

	catalogFile = "catalog.yaml"
	storageURL = "https://bkt.s3.us-east-1.amazonaws.com/my-block/v1/"

	fake := &fakeProvider{uploaded: map[string]string{}}
	err := runCatalogUpload(context.Background(), fake, "my-block/v1", dir)
	require.Error(t, err)
	assert.Contains(t, err.Error(), "no media")
}

func TestRunCatalogUpload_NotFound(t *testing.T) {
	saveFlags(t)

	catalogFile = "catalog.yaml"
	fake := &fakeProvider{uploaded: map[string]string{}}
	err := runCatalogUpload(context.Background(), fake, "", t.TempDir())
	require.Error(t, err)
	assert.Contains(t, err.Error(), "catalog file not found")
}
