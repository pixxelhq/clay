package bootstrap

import (
	"io/fs"
	"os"
	"strings"
	"text/template"
	"unicode"
)

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

func isAlpha(s string) bool {
	for _, r := range s {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return true
}

func verifyModelName(modelName string) {
	if !isAlpha(modelName) {
		panic("Model name can only contain alphabets")
	}
}

func checkError(e error) {
	if e != nil {
		panic(e)
	}
}

// Recursively deletes an entire directory
func deleteDir(path string) {
	_ = os.RemoveAll(path)
}

// Copies a file from src to dst
func Copy(filesystem fs.FS, src string, dst string) {
	// Read all content of src to data, may cause OOM for a large file.
	data, err := fs.ReadFile(filesystem, src)
	checkError(err)
	// Write data to dst
	err = os.WriteFile(dst, data, 0644)
	checkError(err)
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
	checkError(err)
	defer outFile.Close()
	templateString, err := readFileToString(filesystem, templatePath)
	checkError(err)
	createTemplate("template", templateString).Execute(outFile, data)
	return nil
}

func getTemplateData(modelName string) map[string]TemplateData {
	data := map[string]TemplateData{
		"model.py":                 Model{ModelName: modelName},
		"entry.py":                 Entry{ModelName: modelName},
		"README.md":                Readme{Name: modelName},
		"model_specification.yaml": ModelSpecification{Name: modelName},
		"test_model.py":            TestModel{ModelName: modelName},
		"Makefile":                 Makefile{ModelName: modelName},
	}
	return data
}
