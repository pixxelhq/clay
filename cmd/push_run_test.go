package cmd

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/pixxelhq/clay/pkg/config"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func pushRunProject(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	require.NoError(t, os.WriteFile(filepath.Join(dir, "clay.yaml"), []byte("name: my-block\nversion: v0.1.0\n"), 0644))
	return dir
}

func TestDockerRegistryFromFlagOrEnv(t *testing.T) {
	t.Setenv("CLAY_DOCKER_REGISTRY", "env.example.com")
	assert.Equal(t, "flag.example.com", dockerRegistryFromFlagOrEnv("flag.example.com"))
	assert.Equal(t, "env.example.com", dockerRegistryFromFlagOrEnv(""))

	t.Setenv("CLAY_DOCKER_REGISTRY", "")
	assert.Equal(t, "", dockerRegistryFromFlagOrEnv(""))
}

func TestImageToPush_DefaultUsesRegistry(t *testing.T) {
	t.Setenv("CLAY_DOCKER_REGISTRY", "")

	local, target, err := imageToPush(nil, "registry.example.com", pushRunProject(t))

	require.NoError(t, err)
	assert.Equal(t, "my-block:v0.1.0", local)
	assert.Equal(t, "registry.example.com/my-block:v0.1.0", target)
}

func TestImageToPush_DefaultReadsRegistryFromEnv(t *testing.T) {
	t.Setenv("CLAY_DOCKER_REGISTRY", "env.example.com")

	_, target, err := imageToPush(nil, "", pushRunProject(t))

	require.NoError(t, err)
	assert.Equal(t, "env.example.com/my-block:v0.1.0", target)
}

func TestImageToPush_DefaultWithoutRegistry(t *testing.T) {
	t.Setenv("CLAY_DOCKER_REGISTRY", "")

	_, _, err := imageToPush(nil, "", pushRunProject(t))

	require.Error(t, err)
	assert.Equal(t, "no Docker registry given\nhint: pass --docker-registry <host> or set CLAY_DOCKER_REGISTRY, or pass the full image name", err.Error())
}

func TestImageToPush_ExplicitImageNeedsNoProject(t *testing.T) {
	local, target, err := imageToPush([]string{"registry.example.com/my-block:v0.1.0"}, "", t.TempDir())

	require.NoError(t, err)
	assert.Equal(t, "registry.example.com/my-block:v0.1.0", local)
	assert.Equal(t, local, target)
}

func TestImageToPush_ExplicitImageWithoutRegistry(t *testing.T) {
	_, _, err := imageToPush([]string{"my-block:v0.1.0"}, "", t.TempDir())

	require.Error(t, err)
	assert.Equal(t, "image my-block:v0.1.0 has no registry, so Docker would push it to docker.io/library, where only official images can be pushed\n"+
		"hint: pass the full name, for example registry.example.com/my-block:v0.1.0, or run 'clay push --docker-registry <host>' in the project", err.Error())
}

func TestImageToPush_ImageAndRegistryFlag(t *testing.T) {
	_, _, err := imageToPush([]string{"registry.example.com/my-block:v0.1.0"}, "other.example.com", t.TempDir())

	require.Error(t, err)
	assert.Equal(t, "use either an image name or --docker-registry, not both\n"+
		"hint: 'clay push --docker-registry <host>' pushes <name>:<version> from clay.yaml", err.Error())
}

func TestImageToRun(t *testing.T) {
	cfg := &config.Config{Name: "my-block", Version: "v0.1.0"}

	assert.Equal(t, "my-block:v0.1.0", imageToRun(nil, cfg))
	assert.Equal(t, "other:1", imageToRun([]string{"other:1"}, cfg))
}
