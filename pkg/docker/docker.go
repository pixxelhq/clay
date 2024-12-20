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

func Build(buildtag, dockerfilePath string, secrets, buildArgs []string, noCache bool) error {
	args := []string{}
	args = append(args, "docker", "build", "-t", buildtag, "-f", dockerfilePath, ".")

	if noCache {
		args = append(args, "--no-cache")
	}

	for _, secret := range secrets {
		args = append(args, "--secret", secret)
	}

	for _, buildArg := range buildArgs {
		args = append(args, "--build-arg", buildArg)
	}

	buildCmd := exec.Command("sudo", args...)
	buildCmd.Env = append(os.Environ(), "DOCKER_BUILDKIT=1")
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
