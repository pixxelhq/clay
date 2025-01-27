package docker

import (
	_ "embed"
	"fmt"
	"html/template"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/example/clay/pkg/config"
)

var (

	//go:embed templates/pip.tmpl
	pipTemplate string

	//go:embed templates/conda.tmpl
	condaTemplate string

	ClayVersion string
)

type dockerFileConfig struct {
	PythonVersion  string
	SrcCodeDir     string
	ClayVersion    string
	DependencyFile string
	AptGetPkgs     []string
	UseCuda        bool
}

func CreateDockerFile(projectDir, outputDir string, cfg *config.Config) (string, error) {
	dc := &dockerFileConfig{
		PythonVersion:  cfg.Bulid.PythonVersion,
		ClayVersion:    ClayVersion,
		SrcCodeDir:     projectDir,
		DependencyFile: cfg.Bulid.DependencyFile,
		AptGetPkgs:     cfg.Bulid.AptGetPkgs,
		UseCuda:        cfg.Bulid.Conda,
	}

	dockerTemplate := pipTemplate
	if dc.UseCuda {
		dockerTemplate = condaTemplate
	}

	funcMap := template.FuncMap{
		"join": func(list []string) string {
			return strings.Join(list, " ")
		},
	}

	dockerfilePath := filepath.Join(outputDir, "Dockerfile")
	dockerfile, err := os.Create(dockerfilePath)
	if err != nil {
		return "", err
	}

	tmpl, err := template.New("Dockerfile").Funcs(funcMap).Parse(dockerTemplate)
	if err != nil {
		return "", err
	}
	fmt.Printf("creating dockerfile in %s", outputDir)
	if err := tmpl.Execute(dockerfile, dc); err != nil {
		return "", err
	}

	return dockerfilePath, nil
}

func GetDockerFile() (string, error) {
	cwd, err := os.Getwd()
	if err != nil {
		return "", err
	}
	dockerfilePath := filepath.Join(cwd, "Dockerfile")
	_, err = os.Stat(dockerfilePath)
	if os.IsNotExist(err) {
		return "", ErrDoesNotExists
	}
	if err != nil {
		return "", err
	}

	return dockerfilePath, nil
}

type BuildFlags struct {
	Secrets, BuildArgs, Platforms []string
	NoCache                       bool
}

func Build(buildtag, dockerfilePath string, bf BuildFlags) error {
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

	env := append(os.Environ(), "DOCKER_BUILDKIT=1")

	buildCmd := exec.Command("sudo", append([]string{"-E", "docker"}, args...)...)
	buildCmd.Env = env
	buildCmd.Stdout = os.Stdout
	buildCmd.Stderr = os.Stderr

	return buildCmd.Run()
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

func Run(image string, args []string, cfg *config.Config) error {
	fmt.Printf("🧐 Serching image %s \n", image)
	err := ImageExists(image)
	if err == ErrDoesNotExists {
		return fmt.Errorf("oops image %s does not exists. First build the image using `clay build` command to build this image", image)
	}

	runArgs := buildDockerRunArgs(image, cfg)
	runCmd := exec.Command("docker", append(runArgs, args...)...)
	runCmd.Stdout = os.Stdout
	runCmd.Stderr = os.Stderr

	return runCmd.Run()
}

func buildDockerRunArgs(image string, cfg *config.Config) []string {
	args := []string{"run", "--rm"}
	if cfg.Gpu {
		args = append(args, "--runtime", "nvidia", "--gpus", "all")
	}

	return append(args, image)
}
