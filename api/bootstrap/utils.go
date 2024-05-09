package bootstrap

import (
	"io/fs"
	"os"
	"strings"
	"text/template"
	"unicode"

	"errors"
)

var Version string

type TemplateData interface{}

type Readme struct {
	Name string
}

type ModelSpecification Readme

type Entry struct {
	ModelName string
}

type Model Entry

type TestModel Entry

type Makefile Entry

type GithubWorkflow struct {
	ModelName string
	Version   string
}

type PyProject Entry

func isAlpha(s string) bool {
	for _, r := range s {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return true
}

func verifyModelName(modelName string) error {
	if !isAlpha(modelName) {
		err := errors.New("Model name can only contain alphabets")
		return err
	}
	return nil
}

// Recursively deletes an entire directory
func deleteDir(path string) {
	_ = os.RemoveAll(path)
}

// Copies a file from src to dst
func Copy(filesystem fs.FS, src string, dst string) error {
	// Read all content of src to data, may cause OOM for a large file.
	data, err := fs.ReadFile(filesystem, src)
	if err != nil {
		return err
	}
	// Write data to dst
	err = os.WriteFile(dst, data, 0644)
	if err != nil {
		return err
	}
	return nil
}

// Reads and returns `filepath`'s contents in a string
func readFileToString(filesystem fs.FS, filepath string) (string, error) {
	data, err := fs.ReadFile(filesystem, filepath)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

func createTemplate(name, t string) *template.Template {
	funcMap := template.FuncMap{
		"ToUpper": strings.ToUpper,
		"ToLower": strings.ToLower,
	}
	return template.Must(template.New(name).Funcs(funcMap).Parse(t))
}

func writeTemplateToFile(filesystem fs.FS, templatePath string, outputPath string, data interface{}) error {
	// TODO: write better error messages
	outFile, err := os.Create(outputPath)
	if err != nil {
		return err
	}
	defer outFile.Close()
	templateString, err := readFileToString(filesystem, templatePath)
	if err != nil {
		return err
	}
	err = createTemplate("template", templateString).Execute(outFile, data)
	if err != nil {
		return err
	}
	return nil
}

func getTemplateData(titlemodelName string, specmodelName string) map[string]TemplateData {
	data := map[string]TemplateData{
		"model.py":                      Model{ModelName: titlemodelName},
		"entry.py":                      Entry{ModelName: titlemodelName},
		"README.md":                     Readme{Name: titlemodelName},
		"model_specification_dev.yaml":  ModelSpecification{Name: specmodelName},
		"model_specification_prod.yaml": ModelSpecification{Name: specmodelName},
		"model_specification_stg.yaml":  ModelSpecification{Name: specmodelName},
		"test_model.py":                 TestModel{ModelName: titlemodelName},
		"Makefile":                      Makefile{ModelName: titlemodelName},
		"test_main.py":                  TestModel{ModelName: titlemodelName},
		"pyproject.toml":                PyProject{ModelName: titlemodelName},
		"add-block-dev-stg.yaml":        GithubWorkflow{ModelName: specmodelName, Version: Version},
		"build.yaml":                    GithubWorkflow{ModelName: specmodelName},
		"update-latest-block.yaml":      GithubWorkflow{ModelName: specmodelName},
		"add-block-prod.yaml":           GithubWorkflow{ModelName: specmodelName, Version: Version},
		"add-model-readme.yaml":         GithubWorkflow{ModelName: specmodelName},
	}
	return data
}
