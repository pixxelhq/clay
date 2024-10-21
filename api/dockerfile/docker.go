package dockerfile

import (
	_ "embed"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"text/template"

	"github.com/example/orchestrator/core/v1alpha1/block"
)

var (
	//go:embed templates/pip.tmpl
	pipTemplate string

	//go:embed templates/conda.tmpl
	condaTemplate string
)

var Version string

type DockerfileData struct {
	Build                  block.Build
	RuntimeOpts            block.Runtime
	UseHttpRunner          bool
	SourceCodeFolder       string
	ModelSpecificationPath string
	Version                string
}

func buildDockerfile(useHttpRunner bool, build block.Build, runtimeOpts block.Runtime, OutputFolder, SourceCodeFolder, ModelSpecificationPath string) error {
	data := DockerfileData{
		Build:                  build,
		RuntimeOpts:            runtimeOpts,
		UseHttpRunner:          useHttpRunner,
		SourceCodeFolder:       SourceCodeFolder,
		ModelSpecificationPath: ModelSpecificationPath,
		Version:                Version,
	}

	funcMap := template.FuncMap{
		"join": func(list []string) string {
			return strings.Join(list, " ")
		},
	}

	var tmpl *template.Template
	var err error
	var dockerTemplate = pipTemplate

	if runtimeOpts.Gpu || build.Conda {
		dockerTemplate = condaTemplate
	}

	tmpl, err = template.New("Dockerfile").Funcs(funcMap).Parse(dockerTemplate)
	if err != nil {
		return err
	}

	// Write Dockerfile to output folder
	dockerfilePath := filepath.Join(OutputFolder, "Dockerfile")
	dockerfile, err := os.Create(dockerfilePath)
	if err != nil {
		return err
	}
	defer dockerfile.Close()

	err = tmpl.Execute(dockerfile, data)
	if err != nil {
		return err
	}

	fmt.Println("Use the below command in your terminal to build the docker container:")
	fmt.Println("make docker-image")
	return nil
}

func GenerateDockerfile(modelSpecificationPath string, sourceCodeFolder string, useHttpRunner bool) error {
	outputFolder := "."
	modelSpecificationPath, err := filepath.Rel(outputFolder, modelSpecificationPath)
	if err != nil {
		return err
	}
	if sourceCodeFolder == "" {
		fmt.Println("No `sourceCodeFolder` provided. Using \"./src\" by default")
		sourceCodeFolder = "./src"
	}
	sourceCodeFolder, err = filepath.Rel(outputFolder, sourceCodeFolder)
	if err != nil {
		return err
	}

	build, err := getBuildFromConfigFile(modelSpecificationPath)
	if err != nil {
		return err
	}

	runtimeOpts, err := getRuntimeOptsFromConfigFile(modelSpecificationPath)
	if err != nil {
		return err
	}

	if runtimeOpts.Gpu && !build.Conda {
		return errors.New(`
			Models with GPU requirement need to use conda.
			Please set Conda to True in build options.
			`)

	}

	if !build.Gdal {
		return errors.New(`
			As of now, it is not possible to exclude GDAL from the Model Container.
			Clay requires Matter which in turn requires geospatial libraries that require GDAL.
			Please set gdal to True in your build options.
		`)
	}

	err = buildDockerfile(useHttpRunner, build, runtimeOpts, outputFolder, sourceCodeFolder, modelSpecificationPath)
	return err

}
