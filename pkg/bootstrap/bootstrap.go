package bootstrap

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
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

func getProjectTemplateDir() string {
	_, filename, _, _ := runtime.Caller(0)
	dir := filepath.Dir(filename)

	// Append the folder name to the path
	folder := "templates/full"
	return filepath.Join(dir, folder)
}

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
func Copy(src string, dst string) {
	// Read all content of src to data, may cause OOM for a large file.
	data, err := os.ReadFile(src)
	checkError(err)
	// Write data to dst
	err = os.WriteFile(dst, data, 0644)
	checkError(err)
}

// Reads and returns `filepath`'s contents in a string
func ReadFileToString(filepath string) (string, error) {
	data, err := os.ReadFile(filepath)
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

func writeTemplateToFile(templatePath string, outputPath string, data interface{}) error {
	// TODO: write better error messages
	outFile, err := os.Create(outputPath)
	checkError(err)
	defer outFile.Close()
	templateString, err := ReadFileToString(templatePath)
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
	}
	return data
}

// Bootstraps a project in `outputDir` with `modelName` as a filler
// in appropriate locations in code and configuration
func CreateProject(outputDir, modelName string) error {
	verifyModelName(modelName)
	data := getTemplateData(modelName)
	outputDir = filepath.Join(outputDir, modelName)
	fmt.Printf("Cleaning up %s ...\n-----------------\n", outputDir)
	deleteDir(outputDir)
	// Create the output directory if it doesn't exist
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		fmt.Println(err)
	}

	// Walk through the project template directory
	templateDir := getProjectTemplateDir()
	err := filepath.Walk(templateDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		relPath, _ := filepath.Rel(templateDir, path)
		outPath := filepath.Join(outputDir, relPath)
		if relPath == "." {
			return nil
		}
		if info.IsDir() {
			if err := os.Mkdir(outPath, 0755); err != nil {
				fmt.Println(outPath, err)
			}
		} else {
			_data, ok := data[filepath.Base(path)]
			if ok {
				writeTemplateToFile(path, outPath, _data)
			} else {
				Copy(path, outPath)
			}
		}
		fmt.Println("Created:", outPath)
		return nil
	})

	if err != nil {
		return err
	}

	fmt.Printf("\n[IMPORTANT] To begin,\n1. Create and activate your Python environment.\n2. Run `make setup` in your project directory\n\n")
	return nil
}

// TODO: Write tests
