package docker

import (
	"bytes"
	"os"
	"path/filepath"
	"regexp"
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
		PythonVersion:  "3.11",
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

	targetStr := "FROM python:3.11.18-slim-trixie"
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "COPY requirements.txt ."
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = `ENTRYPOINT ["python3", "entry.py"]`
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "apt-get install -y --no-install-recommends libgl1 wget"
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "COPY --from=ghcr.io/astral-sh/uv:" + uvVersion + " /uv /uvx /usr/local/bin/"
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
		PythonVersion:  "3.11",
		DependencyFile: "conda.yaml",
		AptGetPkgs:     []string{"libgl1"},
		Cuda:           true,
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

	targetStr := "FROM mambaorg/micromamba:1.5.9-focal-cuda-11.3.1"
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "COPY conda.yaml ."
	if !strings.Contains(string(content), targetStr) {
		t.Errorf("Dockerfile does not contain expected line: %s", targetStr)
	}

	targetStr = "COPY --from=ghcr.io/astral-sh/uv:" + uvVersion + " /uv /uvx /usr/local/bin/"
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

func TestRenderDockerfile_WritesValuesAsIs(t *testing.T) {
	cfg := &config.Config{
		Bulid: &config.Build{
			PythonVersion:  "3.10",
			DependencyFile: "requirements.txt",
			AptGetPkgs:     []string{"g++", "a&b", "<x>", `"quoted"`, "'single'"},
		},
	}

	var buf bytes.Buffer
	require.NoError(t, RenderDockerfile(&buf, "src", cfg))

	assert.Contains(t, buf.String(), `install -y --no-install-recommends g++ a&b <x> "quoted" 'single'`)
}

func TestRenderDockerfile_NoBuildSection(t *testing.T) {
	var buf bytes.Buffer
	err := RenderDockerfile(&buf, "src", &config.Config{})
	require.Error(t, err)
	assert.Contains(t, err.Error(), "no `build` section")
}

func TestRenderDockerfile_PythonVersion(t *testing.T) {
	tests := []struct {
		version  string
		wantFrom string
		wantErr  bool
	}{
		{version: "3.10", wantFrom: "FROM python:3.10.22-slim-trixie"},
		{version: "3.11", wantFrom: "FROM python:3.11.18-slim-trixie"},
		{version: "3.12", wantFrom: "FROM python:3.12.16-slim-trixie"},
		{version: "", wantFrom: "FROM python:3.10.22-slim-trixie"},
		{version: "3.9", wantErr: true},
		{version: "3.13", wantErr: true},
		{version: "3.10.14", wantErr: true},
	}
	for _, tt := range tests {
		t.Run(tt.version, func(t *testing.T) {
			cfg := &config.Config{Bulid: &config.Build{PythonVersion: tt.version, DependencyFile: "requirements.txt"}}

			var buf bytes.Buffer
			err := RenderDockerfile(&buf, "src", cfg)
			if tt.wantErr {
				require.Error(t, err)
				assert.Contains(t, err.Error(), "build.python-version")
				assert.Contains(t, err.Error(), "3.10, 3.11, 3.12")
				assert.Empty(t, buf.String())
				return
			}
			require.NoError(t, err)
			assert.True(t, strings.HasPrefix(buf.String(), tt.wantFrom+"\n"), buf.String())
		})
	}
}

func renderBuild(t *testing.T, build *config.Build) (string, error) {
	t.Helper()
	build.DependencyFile = "requirements.txt"
	var buf bytes.Buffer
	err := RenderDockerfile(&buf, "src", &config.Config{Bulid: build})
	return buf.String(), err
}

func TestRenderDockerfile_Gdal(t *testing.T) {
	tests := []struct {
		version  string
		wantFrom string
	}{
		{version: "3.10", wantFrom: "FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.5"},
		{version: "3.12", wantFrom: "FROM ghcr.io/osgeo/gdal:ubuntu-small-3.12.4"},
		{version: "", wantFrom: "FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.5"},
	}
	for _, tt := range tests {
		t.Run(tt.version, func(t *testing.T) {
			out, err := renderBuild(t, &config.Build{PythonVersion: tt.version, Gdal: true})
			require.NoError(t, err)
			assert.True(t, strings.HasPrefix(out, tt.wantFrom+"\n"), out)
			assert.Contains(t, out, "UV_BREAK_SYSTEM_PACKAGES=1")
			assert.NotContains(t, out, "apt-get")
		})
	}

	out, err := renderBuild(t, &config.Build{PythonVersion: "3.12"})
	require.NoError(t, err)
	assert.NotContains(t, out, "osgeo")
	assert.NotContains(t, out, "UV_")
}

func TestRenderDockerfile_GdalPython311(t *testing.T) {
	var warnings bytes.Buffer
	warnOut = &warnings
	t.Cleanup(func() { warnOut = os.Stderr })

	out, err := renderBuild(t, &config.Build{PythonVersion: "3.11", Gdal: true})
	require.NoError(t, err)
	assert.True(t, strings.HasPrefix(out, "FROM python:3.11.18-slim-trixie\n"), out)
	assert.NotContains(t, out, "UV_")
	assert.Contains(t, warnings.String(), "no OSGeo GDAL image has Python 3.11")
}

func TestRenderDockerfile_CudaPythonAndGdal(t *testing.T) {
	out, err := renderBuild(t, &config.Build{PythonVersion: "3.12", Cuda: true})
	require.NoError(t, err)
	assert.True(t, strings.HasPrefix(out, "FROM mambaorg/micromamba:"), out)
	assert.Contains(t, out, "--file requirements.txt -y \\\n    \"python=3.12\"\n")

	out, err = renderBuild(t, &config.Build{PythonVersion: "3.11", Cuda: true, Gdal: true})
	require.NoError(t, err)
	assert.True(t, strings.HasPrefix(out, "FROM mambaorg/micromamba:"), out)
	assert.Contains(t, out, "--file requirements.txt -y \\\n    \"python=3.11\" gdal\n")
	assert.NotContains(t, out, "UV_BREAK_SYSTEM_PACKAGES")

	out, err = renderBuild(t, &config.Build{Cuda: true, AptGetPkgs: []string{"wget", "g++"}})
	require.NoError(t, err)
	assert.Contains(t, out, "apt-get install -y --no-install-recommends libgl1 wget g++ &&")
}

func TestRenderDockerfile_NonRoot(t *testing.T) {
	for _, build := range []*config.Build{{}, {Gdal: true}, {Cuda: true}} {
		out, err := renderBuild(t, build)
		require.NoError(t, err)
		users := regexp.MustCompile(`(?m)^USER .*$`).FindAllString(out, -1)
		require.NotEmpty(t, users, out)
		assert.NotEqual(t, "USER root", users[len(users)-1], out)
		assert.Contains(t, out, "ENV PYTHONUNBUFFERED=1")
	}
}

func TestRenderDockerfile_Cuda(t *testing.T) {
	var warnings bytes.Buffer
	warnOut = &warnings
	t.Cleanup(func() { warnOut = os.Stderr })

	out, err := renderBuild(t, &config.Build{Cuda: true})
	require.NoError(t, err)
	assert.True(t, strings.HasPrefix(out, "FROM mambaorg/micromamba:"), out)
	assert.Empty(t, warnings.String())

	conda, err := renderBuild(t, &config.Build{Conda: true})
	require.NoError(t, err)
	assert.Equal(t, out, conda)
	assert.Contains(t, warnings.String(), "build.conda is deprecated")
	assert.Contains(t, warnings.String(), "use build.cuda instead")
}

func TestBuildDockerRunArgs_Gpu(t *testing.T) {
	args := buildDockerRunArgs("demo:test", nil, &config.Config{Gpu: true})
	assert.Equal(t, []string{"run", "--rm", "--gpus", "all", "demo:test"}, args)

	args = buildDockerRunArgs("demo:test", nil, &config.Config{})
	assert.Equal(t, []string{"run", "--rm", "demo:test"}, args)
}
