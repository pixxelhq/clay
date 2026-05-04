package docker

import (
	"os"
	"strings"
	"testing"

	"github.com/pixxelhq/clay-framework/pkg/config"
	"github.com/stretchr/testify/require"
)

func TestCreateDockerFileForPip(t *testing.T) {
	// Setup
	outputDir := t.TempDir()
	build := &config.Build{
		PythonVersion:  "3.8",
		DependencyFile: "requirements.txt",
		AptGetPkgs:     []string{"libgl1", "wget"},
	}
	cfg := &config.Config{
		Name:  "test-app",
		Bulid: build,
	}

	dockerfilePath, err := CreateDockerFile("src", outputDir, cfg)
	require.NoError(t, err)

	_, err = os.Stat(dockerfilePath)
	require.NoError(t, err)

	content, err := os.ReadFile(dockerfilePath)
	require.NoError(t, err)

	targetStr := "COPY requirements.txt ."
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "apt-get install -y python3.8 python3-pip libgl1 wget"
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/"
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "uv pip install --system --no-cache"
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}
}

func TestCreateDockerFileForConda(t *testing.T) {
	// Setup
	outputDir := t.TempDir()
	build := &config.Build{
		PythonVersion:  "3.8",
		DependencyFile: "conda.yaml",
		AptGetPkgs:     []string{"libgl1"},
		Conda:          true,
	}
	cfg := &config.Config{
		Name:  "test-app",
		Bulid: build,
	}

	dockerfilePath, err := CreateDockerFile("src", outputDir, cfg)
	require.NoError(t, err)

	_, err = os.Stat(dockerfilePath)
	require.NoError(t, err)

	content, err := os.ReadFile(dockerfilePath)
	require.NoError(t, err)

	targetStr := "FROM mambaorg/micromamba:1-focal-cuda-11.3.1"
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "COPY conda.yaml ."
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/"
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "uv pip install --system --no-cache"
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}
}
