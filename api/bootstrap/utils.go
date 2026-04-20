package bootstrap

import (
	"io/fs"
	"os"
	"strings"
	"text/template"
	"unicode"

	"errors"

	"github.com/iancoleman/strcase"
)

var Version string

type TemplateData interface{}

type Config struct {
	Name string
}

type Readme struct {
	Name string
}

type BlockSpecification Readme

type Entry struct {
	BlockName string
}

type Block Entry

type TestBlock Entry

type Makefile Entry

type GithubWorkflow struct {
	BlockName string
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

func verifyBlockName(blockName string) error {
	if !isAlpha(blockName) {
		err := errors.New("Block name can only contain alphabets")
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
		"ToSnake": strcase.ToSnake,
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

func getTemplateData(titleBlockName string, specBlockName string) map[string]TemplateData {
	data := map[string]TemplateData{
		"src/block.py":                          Block{BlockName: titleBlockName},
		"src/entry.py":                          Entry{BlockName: titleBlockName},
		"README.md":                             Readme{Name: titleBlockName},
		"tests/test_block.py":                   TestBlock{BlockName: titleBlockName},
		"Makefile":                               Makefile{BlockName: titleBlockName},
		"tests/test_main.py":                    TestBlock{BlockName: titleBlockName},
		"pyproject.toml":                         PyProject{BlockName: titleBlockName},
		".github/workflows/benchmark.yaml":      GithubWorkflow{BlockName: specBlockName, Version: Version},
		".github/workflows/build.yaml":          GithubWorkflow{BlockName: specBlockName, Version: Version},
		".github/workflows/publish.yaml":        GithubWorkflow{BlockName: specBlockName, Version: Version},
		"clay.yaml":                              Config{Name: titleBlockName},
	}
	return data
}
