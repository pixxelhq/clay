package bootstrap

import (
	"embed"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	"github.com/pixxelhq/clay/pkg/blockname"
)

// Embedding Templates in final build

//go:embed all:templates/full
var fullTemplate embed.FS

const fullTemplateRoot = "templates/full"

var ErrProjectDirNotEmpty = errors.New("already exists and is not empty")

// Bootstraps a project in `outputDir` with `blockName` as a filler
// in appropriate locations in code and configuration. `outputDir` is the
// project folder itself.
func CreateProject(outputDir, blockName string, force bool) error {
	names, err := blockname.Parse(blockName)
	if err != nil {
		return err
	}
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
		return err
	}

	// Walk through the project template directory. Template paths are
	// slash-separated on every OS (io/fs rules); they are converted to OS
	// paths only when joined to outputDir.
	templateFS, err := fs.Sub(fullTemplate, fullTemplateRoot)
	if err != nil {
		return err
	}
	err = fs.WalkDir(templateFS, ".", func(relPath string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		// rename the template's top-level src/ to the block package; only the
		// template-relative path is touched, never the user's outputDir
		outRel := relPath
		if outRel == "src" || strings.HasPrefix(outRel, "src/") {
			outRel = names.Module + strings.TrimPrefix(outRel, "src")
		}
		outPath := filepath.Join(outputDir, filepath.FromSlash(outRel))
		_, statErr := os.Stat(outPath)
		existed := statErr == nil
		if d.IsDir() {
			if err := os.MkdirAll(outPath, 0755); err != nil {
				return err
			}
			if !existed {
				fmt.Println("Created:", outPath)
			}
			return nil
		}

		if templatedFiles[relPath] {
			if err := writeTemplateToFile(templateFS, relPath, outPath, names); err != nil {
				return err
			}
		} else if err := Copy(templateFS, relPath, outPath); err != nil {
			return err
		}
		if existed {
			fmt.Println("Overwrote:", outPath)
		} else {
			fmt.Println("Created:", outPath)
		}
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
