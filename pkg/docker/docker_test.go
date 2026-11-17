package docker

import (
	"os"
	"path/filepath"
	"runtime"
	"slices"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/pixxelhq/clay/pkg/config"
	"github.com/stretchr/testify/assert"
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

// fakeDocker puts a `docker` script on PATH that writes stderr and exits
// with exitCode, so CheckDaemon can be tested without a Docker daemon.
func fakeDocker(t *testing.T, stderr string, exitCode int) {
	t.Helper()
	dir := t.TempDir()
	script := "#!/bin/sh\nprintf '%s\\n' \"$FAKE_DOCKER_STDERR\" >&2\nexit " + strconv.Itoa(exitCode) + "\n"
	require.NoError(t, os.WriteFile(filepath.Join(dir, "docker"), []byte(script), 0755))
	t.Setenv("PATH", dir)
	t.Setenv("FAKE_DOCKER_STDERR", stderr)
}

func TestCheckDaemon_Reachable(t *testing.T) {
	fakeDocker(t, "", 0)
	assert.NoError(t, CheckDaemon())
}

func TestCheckDaemon_DockerNotInstalled(t *testing.T) {
	t.Setenv("PATH", t.TempDir())

	err := CheckDaemon()
	require.ErrorIs(t, err, ErrDaemonUnavailable)
	assert.Contains(t, err.Error(), "executable file not found")
	assert.Contains(t, err.Error(), "hint: "+hintStartDocker)
}

func TestCheckDaemon_DaemonNotRunning(t *testing.T) {
	cause := "Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?"
	fakeDocker(t, cause, 1)

	err := CheckDaemon()
	require.ErrorIs(t, err, ErrDaemonUnavailable)
	assert.Contains(t, err.Error(), cause)
	assert.Contains(t, err.Error(), "hint: "+hintStartDocker)
}

func TestCheckDaemon_PermissionDenied(t *testing.T) {
	cause := "permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock"
	fakeDocker(t, cause, 1)

	err := CheckDaemon()
	require.ErrorIs(t, err, ErrDaemonUnavailable)
	assert.Contains(t, err.Error(), cause)

	wantHint := hintStartDocker
	if runtime.GOOS == "linux" {
		wantHint = hintDockerGroup
	}
	assert.Contains(t, err.Error(), "hint: "+wantHint)
}

func TestCheckDaemon_Timeout(t *testing.T) {
	dir := t.TempDir()
	require.NoError(t, os.WriteFile(filepath.Join(dir, "docker"), []byte("#!/bin/sh\nexec /bin/sleep 5\n"), 0755))
	t.Setenv("PATH", dir)

	old := daemonCheckTimeout
	daemonCheckTimeout = 100 * time.Millisecond
	t.Cleanup(func() { daemonCheckTimeout = old })

	err := CheckDaemon()
	require.ErrorIs(t, err, ErrDaemonUnavailable)
	assert.Contains(t, err.Error(), "docker did not respond within 100ms")
	assert.Contains(t, err.Error(), "hint: "+hintStartDocker)
}

func TestBuildCommand_RunsDockerWithoutSudo(t *testing.T) {
	cmd := buildCommand("demo:test", "Dockerfile", BuildFlags{NoCache: true})

	assert.Equal(t, []string{"docker", "build", "-t", "demo:test", "-f", "Dockerfile", ".", "--no-cache"}, cmd.Args)
	assert.True(t, slices.Contains(cmd.Env, "DOCKER_BUILDKIT=1"), "DOCKER_BUILDKIT=1 should be set")
}
