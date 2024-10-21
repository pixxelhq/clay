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

type dockerConfig struct {
	PythonVersion  string
	SrcCodeDir     string
	ClayVersion    string
	DependencyFile string
	AptGetPkgs     []string
	UseCuda        bool
}

func CreateDockerFile(projectDir, outputDir string, cfg *config.Config) (string, error) {
	dc := &dockerConfig{
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

func BuildImage(buildtag, dockerfilePath string, secrets, buildArgs []string, noCache bool) error {
	args := []string{}
	args = append(args, "build", "-t", buildtag, "-f", dockerfilePath, ".")

	if noCache {
		args = append(args, "--no-cache")
	}

	for _, secret := range secrets {
		args = append(args, "--secret", secret)
	}

	for _, buildArg := range buildArgs {
		args = append(args, "--build-arg", buildArg)
	}

	buildCmd := exec.Command("docker", args...)
	buildCmd.Stdout = os.Stdout
	buildCmd.Stderr = os.Stderr
	if err := buildCmd.Start(); err != nil {
		return fmt.Errorf("failed to build image: %w", err)
	}

	if err := buildCmd.Wait(); err != nil {
		return fmt.Errorf("failed to build image: %w", err)
	}

	return nil
}
