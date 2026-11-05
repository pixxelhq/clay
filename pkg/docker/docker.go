package docker

import (
	"bytes"
	"context"
	_ "embed"
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
// OSGeo Ubuntu image has Python 3.11, so 3.11 uses pythonImages.
var gdalImages = map[string]string{
	"3.10": "ghcr.io/osgeo/gdal:ubuntu-small-3.8.5",  // Ubuntu 22.04
	"3.12": "ghcr.io/osgeo/gdal:ubuntu-small-3.12.4", // Ubuntu 24.04
}

var warnOut io.Writer = os.Stderr

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
		return fmt.Errorf("clay.yaml has no `build` section")
	}

	pyVersion, err := pythonVersion(cfg.Bulid.PythonVersion)
	if err != nil {
		return err
	}

	if cfg.Bulid.Conda {
		fmt.Fprintln(warnOut, "warning: clay.yaml: build.conda is deprecated and will be removed in the next minor release; use build.cuda instead.")
	}
	useCuda := cfg.Bulid.Cuda || cfg.Bulid.Conda

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

	// With cuda, the conda environment gets python and gdal (see conda.tmpl),
	// so the base image does not change.
	if dc.UseGdal && !useCuda {
		if image, ok := gdalImages[pyVersion]; ok {
			dc.BaseImage = image
		} else {
			fmt.Fprintf(warnOut, "warning: clay.yaml: build.gdal is ignored, because no OSGeo GDAL image has Python %s. The image is %s, without GDAL.\n"+
				"To get GDAL, set build.python-version to \"3.10\" or \"3.12\".\n", pyVersion, dc.BaseImage)
			dc.UseGdal = false
		}
	}

	dockerTemplate := pipTemplate
	if useCuda {
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

func Build(buildtag, dockerfilePath string, bf BuildFlags) error {
	buildCmd := buildCommand(buildtag, dockerfilePath, bf)
	buildCmd.Stdout = os.Stdout
	buildCmd.Stderr = os.Stderr

	return buildCmd.Run()
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
	pushCmd := exec.Command("docker", "push", buildtag)
	pushCmd.Stdout = os.Stdout
	pushCmd.Stderr = os.Stderr

	return pushCmd.Run()
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
		return err
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
		return fmt.Errorf("oops image %s does not exist. First build the image using `clay build` command to build this image", image)
	}
	if err != nil {
		return fmt.Errorf("error while searching image %s: %w", image, err)
	}

	runArgs := buildDockerRunArgs(image, envVars, cfg)
	runCmd := exec.Command("docker", append(runArgs, args...)...)
	runCmd.Stdout = os.Stdout
	runCmd.Stderr = os.Stderr

	return runCmd.Run()
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
