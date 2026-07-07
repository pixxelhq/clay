package catalog

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// repoWith creates a temp model repo containing the given files.
func repoWith(t *testing.T, files ...string) string {
	t.Helper()
	dir := t.TempDir()
	for _, f := range files {
		p := filepath.Join(dir, f)
		require.NoError(t, os.MkdirAll(filepath.Dir(p), 0755))
		require.NoError(t, os.WriteFile(p, []byte("x"), 0644))
	}
	return dir
}

func TestResolvePath_Valid(t *testing.T) {
	dir := repoWith(t, "catalog_readme/thumbnail.png")

	abs, err := ResolvePath(dir, "catalog_readme/thumbnail.png")
	require.NoError(t, err)
	assert.True(t, filepath.IsAbs(abs))
	assert.Equal(t, filepath.Join(dir, "catalog_readme", "thumbnail.png"), abs)
}

func TestResolvePath_Rejections(t *testing.T) {
	dir := repoWith(t, "catalog_readme/thumbnail.png")

	cases := map[string]struct {
		rel     string
		wantErr string
	}{
		"empty path":     {"", "must not be empty"},
		"absolute path":  {"/etc/passwd", "not absolute"},
		"dot-dot escape": {"../outside.png", "escapes the model repo root"},
		"nested escape":  {"catalog_readme/../../outside.png", "escapes the model repo root"},
		"missing file":   {"catalog_readme/missing.png", "does not exist"},
		"directory":      {"catalog_readme", "is a directory"},
	}
	for name, tc := range cases {
		t.Run(name, func(t *testing.T) {
			_, err := ResolvePath(dir, tc.rel)
			require.Error(t, err)
			assert.Contains(t, err.Error(), tc.wantErr)
		})
	}
}

func TestResolvePath_SymlinkEscapeRejected(t *testing.T) {
	outside := t.TempDir()
	require.NoError(t, os.WriteFile(filepath.Join(outside, "secret.png"), []byte("x"), 0644))

	dir := repoWith(t)
	require.NoError(t, os.Symlink(filepath.Join(outside, "secret.png"), filepath.Join(dir, "sneaky.png")))

	_, err := ResolvePath(dir, "sneaky.png")
	require.Error(t, err)
	assert.Contains(t, err.Error(), "outside the model repo root")
}
