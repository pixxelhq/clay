package bootstrap

import (
	"embed"
	"errors"
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

var ErrProjectDirNotEmpty = errors.New("already exists and is not empty")

// Bootstraps a project in `outputDir` with `blockName` as a filler
// in appropriate locations in code and configuration
func CreateProject(outputDir, blockName string, force bool) error {
	err := verifyBlockName(blockName)
	if err != nil {
		return err
	}
	titleblockName := strcase.ToCamel(blockName)
	specblockName := strcase.ToSnake(blockName)
	data := getTemplateData(titleblockName)
	outputDir = filepath.Join(outputDir, specblockName)
	if !force {
		entries, err := os.ReadDir(outputDir)
		if err != nil && !errors.Is(err, fs.ErrNotExist) {
			return err
		}
		if len(entries) > 0 {
			return fmt.Errorf("%s %w", outputDir, ErrProjectDirNotEmpty)
		}
	}
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
		// rename the template's top-level src/ to the block package; only the
		// template-relative path is touched, never the user's outputDir
		outRel := relPath
		if outRel == "src" || strings.HasPrefix(outRel, "src"+string(filepath.Separator)) {
			outRel = specblockName + strings.TrimPrefix(outRel, "src")
		}
		outPath := filepath.Join(outputDir, outRel)
		if d.IsDir() {
			if err := os.MkdirAll(outPath, 0755); err != nil {
				fmt.Println(outPath, err)
			}
			fmt.Println("Created:", outPath)
			return nil
		}

		_data, ok := data[relPath]
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

	fmt.Printf("\n[IMPORTANT] To begin, navigate to your project directory in your terminal:\n1. Based on your requirement, create a python or conda env\n\n")
	fmt.Printf("	Use the below command to create a python virtual env:\n")
	fmt.Print("			curl -LsSf https://astral.sh/uv/install.sh | sh\n")
	fmt.Print("			uv venv\n")
	fmt.Print("			source .venv/bin/activate\n\n")
	fmt.Printf("	Use the below command to create a conda env:\n")
	fmt.Print("			conda create -n envName python=3.9\n")
	fmt.Print("			conda activate envName\n\n")
	fmt.Print("2. Run `make setup` in your project directory")

	return nil
}
