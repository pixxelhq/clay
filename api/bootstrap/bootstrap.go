package bootstrap

import (
	"embed"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"slices"
	"strings"

	"github.com/pixxelhq/clay/pkg/blockname"
)

// Embedding Templates in final build

//go:embed all:templates/full
var fullTemplate embed.FS

const fullTemplateRoot = "templates/full"

var ErrProjectDirNotEmpty = errors.New("already exists and is not empty")

var ClayVersion string

var Options = []string{"catalog", "conda", "pre-commit"}

var optionalFiles = map[string]string{
	"catalog.yaml":            "catalog",
	"conda.yaml":              "conda",
	".pre-commit-config.yaml": "pre-commit",
}

type templateData struct {
	blockname.Names
	ClayVersion   string
	WithCatalog   bool
	WithConda     bool
	WithPreCommit bool
}

// Bootstraps a project in `outputDir` with `blockName` as a filler
// in appropriate locations in code and configuration. `outputDir` is the
// project folder itself. `with` selects the optional parts of the template
// (see Options).
func CreateProject(outputDir, blockName string, force bool, with []string) error {
	names, err := blockname.Parse(blockName)
	if err != nil {
		return err
	}
	selected := map[string]bool{}
	for _, opt := range with {
		if !slices.Contains(Options, opt) {
			return fmt.Errorf("unknown option %q: valid options are %s", opt, strings.Join(Options, ", "))
		}
		selected[opt] = true
	}
	data := templateData{
		Names:         names,
		ClayVersion:   ClayVersion,
		WithCatalog:   selected["catalog"],
		WithConda:     selected["conda"],
		WithPreCommit: selected["pre-commit"],
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
		if opt, ok := optionalFiles[relPath]; ok && !selected[opt] {
			return nil
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
			if err := writeTemplateToFile(templateFS, relPath, outPath, data); err != nil {
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

	fmt.Println("\nNext steps:")
	cwd, cwdErr := os.Getwd()
	absDir, absErr := filepath.Abs(outputDir)
	if cwdErr != nil || absErr != nil || absDir != cwd {
		fmt.Printf("  cd %s\n", outputDir)
	}
	fmt.Println("  python3 -m venv .venv && source .venv/bin/activate")
	fmt.Println("  pip install -r requirements-dev.txt")
	fmt.Println("  python tests/test_block.py   # run the block locally")
	fmt.Println("  clay build                   # build the image")
	fmt.Println("See README.md for more.")

	return nil
}
