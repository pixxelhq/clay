package docker

import (
	"bytes"
	"context"
	_ "embed"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"slices"
	"strings"
	"text/template"
	"time"

	"github.com/pixxelhq/clay/pkg/config"
)

var (

	//go:embed templates/pip.tmpl
	pipTemplate string

	//go:embed templates/conda.tmpl
	condaTemplate string

	ClayVersion string
)

type dockerFileConfig struct {
	BaseImage      string
	PythonVersion  string
	UvVersion      string
	SrcCodeDir     string
	ClayVersion    string
	DependencyFile string
	AptGetPkgs     []string
	UseGdal        bool
}

var supportedPythonVersions = []string{"3.10", "3.11", "3.12"}

const defaultPythonVersion = "3.10"

const uvVersion = "0.13.7"

var pythonImages = map[string]string{
	"3.10": "python:3.10.22-slim-trixie",
	"3.11": "python:3.11.18-slim-trixie",
	"3.12": "python:3.12.16-slim-trixie",
}

// gdalImages are the base images for each build.python-version when gdal is
// true. The GDAL Python bindings in an OSGeo image are built for the system
// Python of its Ubuntu release, so each image has one Python version. No
// OSGeo Ubuntu image has Python 3.11, so gdal does not work with 3.11.
var gdalImages = map[string]string{
	"3.10": "ghcr.io/osgeo/gdal:ubuntu-small-3.8.5",  // Ubuntu 22.04
	"3.12": "ghcr.io/osgeo/gdal:ubuntu-small-3.12.4", // Ubuntu 24.04
}

func pythonVersion(v string) (string, error) {
	if v == "" {
		return defaultPythonVersion, nil
	}
	if !slices.Contains(supportedPythonVersions, v) {
		return "", fmt.Errorf("clay.yaml: build.python-version %q is not supported; use one of %s",
			v, strings.Join(supportedPythonVersions, ", "))
	}
	return v, nil
}

// CreateDockerFile writes the Dockerfile generated from cfg to
// outputDir/Dockerfile and returns its path.
func CreateDockerFile(projectDir, outputDir string, cfg *config.Config) (path string, err error) {
	path = filepath.Join(outputDir, "Dockerfile")
	f, err := os.Create(path)
	if err != nil {
		return "", err
	}
	defer func() {
		if cerr := f.Close(); err == nil && cerr != nil {
			err = cerr
		}
	}()

	if err := RenderDockerfile(f, projectDir, cfg); err != nil {
		return "", err
	}
	return path, nil
}

// RenderDockerfile writes the Dockerfile generated from cfg to w. Values from
// clay.yaml are written as is, without escaping.
func RenderDockerfile(w io.Writer, projectDir string, cfg *config.Config) error {
	if cfg.Bulid == nil {
		return errors.New("clay.yaml has no `build` section")
	}

	pyVersion, err := pythonVersion(cfg.Bulid.PythonVersion)
	if err != nil {
		return err
	}

	dc := &dockerFileConfig{
		BaseImage:      pythonImages[pyVersion],
		PythonVersion:  pyVersion,
		UvVersion:      uvVersion,
		ClayVersion:    ClayVersion,
		SrcCodeDir:     projectDir,
		DependencyFile: cfg.Bulid.DependencyFile,
		AptGetPkgs:     cfg.Bulid.AptGetPkgs,
		UseGdal:        cfg.Bulid.Gdal,
	}

	// With conda, the conda environment gets python and gdal (see conda.tmpl),
	// so the base image does not change.
	if dc.UseGdal && !cfg.Bulid.Conda {
		image, ok := gdalImages[pyVersion]
		if !ok {
			return fmt.Errorf("clay.yaml: build.gdal is not supported with build.python-version %q, because no OSGeo GDAL image has Python %s.\n"+
				"To fix it, do one of these:\n"+
				"  - set build.conda: true (recommended) to install GDAL from conda for Python %s\n"+
				"  - set build.python-version to \"3.10\" or \"3.12\"\n"+
				"  - set build.gdal: false if the block does not import osgeo", pyVersion, pyVersion, pyVersion)
		}
		dc.BaseImage = image
	}

	dockerTemplate := pipTemplate
	if cfg.Bulid.Conda {
		dockerTemplate = condaTemplate
	}

	funcMap := template.FuncMap{
		"join": func(list []string) string {
			return strings.Join(list, " ")
		},
	}

	tmpl, err := template.New("Dockerfile").Funcs(funcMap).Parse(dockerTemplate)
	if err != nil {
		return err
	}
	return tmpl.Execute(w, dc)
}

type BuildFlags struct {
	Secrets, BuildArgs, Platforms []string
	NoCache                       bool
}

// Verbose makes docker build and push stream their output. Otherwise the
// output is shown only when the command fails, as its last lines.
var Verbose bool

const failedOutputLines = 20

func Build(buildtag, dockerfilePath string, bf BuildFlags) error {
	return runDocker(buildCommand(buildtag, dockerfilePath, bf), "docker build", os.Stdout, os.Stderr)
}

func runDocker(cmd *exec.Cmd, name string, stdout, stderr io.Writer) error {
	if Verbose {
		cmd.Stdout, cmd.Stderr = stdout, stderr
		return commandError(name, cmd.Run(), "")
	}
	var output bytes.Buffer
	cmd.Stdout, cmd.Stderr = &output, &output
	err := cmd.Run()
	if err != nil {
		fmt.Fprint(stderr, lastLines(output.String(), failedOutputLines))
	}
	return commandError(name, err, "rerun with --verbose to see the "+strings.TrimPrefix(name, "docker ")+" output")
}

// commandError names the failed command, so that users never see a bare
// "exit status 1".
func commandError(name string, err error, hint string) error {
	if err == nil {
		return nil
	}
	var exitErr *exec.ExitError
	if !errors.As(err, &exitErr) {
		return fmt.Errorf("%s failed: %w", name, err)
	}
	message := fmt.Sprintf("%s failed (exit %d)", name, exitErr.ExitCode())
	if hint != "" {
		message += "\nhint: " + hint
	}
	return errors.New(message)
}

func lastLines(output string, n int) string {
	output = strings.TrimRight(output, "\n")
	if output == "" {
		return ""
	}
	lines := strings.Split(output, "\n")
	if len(lines) > n {
		lines = lines[len(lines)-n:]
	}
	return strings.Join(lines, "\n") + "\n"
}

func buildCommand(buildtag, dockerfilePath string, bf BuildFlags) *exec.Cmd {
	args := []string{}
	args = append(args, "build", "-t", buildtag, "-f", dockerfilePath, ".")

	if bf.NoCache {
		args = append(args, "--no-cache")
	}

	for _, secret := range bf.Secrets {
		args = append(args, "--secret", secret)
	}

	for _, buildArg := range bf.BuildArgs {
		args = append(args, "--build-arg", buildArg)
	}

	for _, p := range bf.Platforms {
		args = append(args, "--platform", p)
	}

	buildCmd := exec.Command("docker", args...)
	buildCmd.Env = append(os.Environ(), "DOCKER_BUILDKIT=1")

	return buildCmd
}

var daemonCheckTimeout = 10 * time.Second

const (
	hintStartDocker = "make sure Docker is installed and running (start Docker Desktop, or the docker service on Linux)"
	hintDockerGroup = "on Linux, add your user to the docker group: https://docs.docker.com/engine/install/linux-postinstall/"
)

// CheckDaemon verifies that the current user can reach the Docker daemon. On
// failure it returns ErrDaemonUnavailable with Docker's message and a hint.
func CheckDaemon() error {
	ctx, cancel := context.WithTimeout(context.Background(), daemonCheckTimeout)
	defer cancel()

	var stderr bytes.Buffer
	cmd := exec.CommandContext(ctx, "docker", "version")
	cmd.Stdout = io.Discard
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err == nil {
		return nil
	}

	cause := strings.TrimSpace(stderr.String())
	if ctx.Err() == context.DeadlineExceeded {
		cause = fmt.Sprintf("docker did not respond within %s", daemonCheckTimeout)
	} else if cause == "" {
		cause = err.Error()
	}
	hint := hintStartDocker
	if runtime.GOOS == "linux" && strings.Contains(strings.ToLower(cause), "permission denied") {
		hint = hintDockerGroup
	}
	return fmt.Errorf("%w: %s\nhint: %s", ErrDaemonUnavailable, cause, hint)
}

func Push(buildtag string) error {
	return runDocker(exec.Command("docker", "push", buildtag), "docker push", os.Stdout, os.Stderr)
}

func ImageExists(image string) error {
	if image == "" {
		return fmt.Errorf("build tag can't be empty")
	}

	listCmd := exec.Command("docker", "images", "-f", fmt.Sprintf("reference=%s", image))

	repositoryName := strings.Split(image, ":")[0]
	grepCmd := exec.Command("grep", repositoryName)

	pipe, err := listCmd.StdoutPipe()
	if err != nil {
		return err
	}
	grepCmd.Stdin = pipe

	if err := listCmd.Start(); err != nil {
		return err
	}

	if err := grepCmd.Start(); err != nil {
		return err
	}

	if err := listCmd.Wait(); err != nil {
		return commandError("docker images", err, "")
	}

	if err := grepCmd.Wait(); err != nil {
		return ErrDoesNotExists
	}

	return nil
}

func Run(image string, args []string, envVars []string, cfg *config.Config) error {
	fmt.Printf("🧐 Searching image %s \n", image)
	err := ImageExists(image)
	if err == ErrDoesNotExists {
		return fmt.Errorf("image %s does not exist\nhint: build it with 'clay build', or pull it with 'docker pull'", image)
	}
	if err != nil {
		return fmt.Errorf("failed to look up image %s: %w", image, err)
	}

	runArgs := buildDockerRunArgs(image, envVars, cfg)
	runCmd := exec.Command("docker", append(runArgs, args...)...)
	runCmd.Stdout = os.Stdout
	runCmd.Stderr = os.Stderr

	return commandError("docker run", runCmd.Run(), "see the block's output above")
}

func buildDockerRunArgs(image string, envVars []string, cfg *config.Config) []string {
	args := []string{"run", "--rm"}
	if cfg.Gpu {
		args = append(args, "--gpus", "all")
	}
	for _, env := range envVars {
		args = append(args, "-e", env)
	}

	return append(args, image)
}
