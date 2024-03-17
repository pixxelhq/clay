package bootstrap

import (
	"embed"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	"github.com/iancoleman/strcase"
)

// Embedding Templates in final build

//go:embed all:templates/full
var fullTemplate embed.FS

const fullTemplateRoot = "templates/full"

// Bootstraps a project in `outputDir` with `modelName` as a filler
// in appropriate locations in code and configuration
func CreateProject(outputDir, modelName string) error {
	err := verifyModelName(modelName)
	if err != nil {
		return err
	}
	titlemodelName := strcase.ToCamel(modelName)
	specmodelName := strings.ToLower(modelName)
	data := getTemplateData(titlemodelName, specmodelName)
	outputDir = filepath.Join(outputDir, modelName)
	fmt.Printf("Cleaning up %s ...\n-----------------\n", outputDir)
	deleteDir(outputDir)
	// Create the output directory if it doesn't exist
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		fmt.Println(err)
	}

	// Walk through the project template directory
	err = fs.WalkDir(fullTemplate, fullTemplateRoot, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		relPath, _ := filepath.Rel(fullTemplateRoot, path)
		outPath := filepath.Join(outputDir, relPath)
		outPath = strings.Replace(outPath, "src", titlemodelName, 1)
		if d.IsDir() {
			if err := os.Mkdir(outPath, 0755); err != nil {
				fmt.Println(outPath, err)
			}
			fmt.Println("Created:", outPath)
			return nil
		}

		_data, ok := data[d.Name()]
		if ok {
			writeTemplateToFile(fullTemplate, path, outPath, _data)
		} else {
			err = Copy(fullTemplate, path, outPath)
			if err != nil {
				return err
			}
		}
		fmt.Println("Created:", outPath)
		return nil
	})

	if err != nil {
		return err
	}

	fmt.Printf("\n[IMPORTANT] To begin,\n1. Create and activate your Python environment.\n2. Make sure you have GDAL on your system and Clay package already installed in your python environment.\n3. Run `make setup` in your project directory\n\n")
	fmt.Printf("To create a new environment:\nOpen your terminal with an existing Python or Conda installation, and use the below command to create an environment:\n\n")
	fmt.Print("python -m venv ./env\n\n")
	return nil
}

// TODO: Write tests
