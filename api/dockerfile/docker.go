package dockerfile

import (
	_ "embed"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"text/template"

	"github.com/example/orchestrator/core/block"
)

//go:embed templates/pip.tmpl
var pipTemplate string

type DockerfileData struct {
	Build                  block.Build
	UseHttpRunner          bool
	SourceCodeFolder       string
	ModelSpecificationPath string
}

func buildDockerfile(useHttpRunner bool, build block.Build, OutputFolder string, SourceCodeFolder string, ModelSpecificationPath string) error {
	data := DockerfileData{
		Build:                  build,
		UseHttpRunner:          useHttpRunner,
		SourceCodeFolder:       SourceCodeFolder,
		ModelSpecificationPath: ModelSpecificationPath,
	}

	funcMap := template.FuncMap{
		"join": func(list []string) string {
			return strings.Join(list, " ")
		},
	}

	template, err := template.New("Dockerfile").Funcs(funcMap).Parse(pipTemplate)
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

	err = template.Execute(dockerfile, data)
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

	if build.Conda {
		return errors.New(`
			Conda support is planned for an upcoming release and is not supported currently.
			Please set Conda to False in your build options.
		`)
	}
	if !build.Gdal {
		return errors.New(`
			As of now, it is not possible to exclude GDAL from the Model Container.
			Clay requires Matter which in turn requires geospatial libraries that require GDAL.
			Please set gdal to True in your build options.
		`)
	}

	err = buildDockerfile(useHttpRunner, build, outputFolder, sourceCodeFolder, modelSpecificationPath)
	if err != nil {
		return err
	}
	return nil
}
