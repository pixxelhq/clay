package bootstrap

import (
	"io/fs"
	"os"
	"text/template"
)

// templatedFiles are the template files rendered with templateData (block
// names, Clay version and --with options); all other files are copied as
// they are.
var templatedFiles = map[string]bool{
	"src/block.py":         true,
	"src/entry.py":         true,
	"README.md":            true,
	"tests/test_block.py":  true,
	"pyproject.toml":       true,
	"clay.yaml":            true,
	"requirements.txt":     true,
	"requirements-dev.txt": true,
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
	return template.Must(template.New(name).Parse(t))
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
