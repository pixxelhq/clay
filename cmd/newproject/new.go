// Package newproject implements the `clay new` and `clay init` commands,
// which scaffold a new block project. The package is named "newproject"
// (not "new") to avoid clashing with Go's built-in new() function.
package newproject

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	"github.com/MakeNowJust/heredoc"
	"github.com/pixxelhq/clay/api/bootstrap"
	bname "github.com/pixxelhq/clay/pkg/blockname"
	"github.com/spf13/cobra"
)

var errDirNotEmpty = errors.New("already exists and is not empty")

var personalHomeFolders = []string{"Desktop", "Documents", "Downloads"}

// NewCmd returns the command that scaffolds a block project in a new or
// empty directory.
func NewCmd() *cobra.Command {
	var name string
	var with []string
	cmd := &cobra.Command{
		Use:   "new <path>",
		Short: "Scaffold a new block project",
		Long: heredoc.Doc(`
			Scaffold a new block project in the directory <path>. The last part of
			the path is used as the block name, unless --name is given.

			The block name is letters, digits, '-' and '_'. my-block, my_block and
			MyBlock all give:

			  clay.yaml name and image   my-block
			  Python package folder      my_block
			  Python class               MyBlock

			The directory must not exist or must be empty. If it already holds files,
			clay new stops with an error and changes nothing; run clay init in the
			directory to make it a block project.

			The project contains only the files every block needs. Use --with to
			add more:

			  catalog      catalog.yaml, to describe the block in a catalog
			  conda        conda.yaml, and clay.yaml set to build with conda
			  pre-commit   .pre-commit-config.yaml, and pre-commit in requirements-dev.txt
		`),
		Example: heredoc.Doc(`
			clay new my-block                # creates ./my-block
			clay new ~/blocks/weather-model  # creates ~/blocks/weather-model
			clay new resnet.v2 --name resnet-v2
			clay new my-block --with catalog,conda
		`),
		Args: cobra.RangeArgs(1, 2),
		RunE: func(cmd *cobra.Command, args []string) error {
			if isDeprecatedForm := len(args) == 2; isDeprecatedForm {
				if name != "" {
					return errors.New("--name cannot be used with the deprecated form 'clay new <path> <name>'")
				}
				return newProjectFromDeprecatedForm(cmd, args[0], args[1], with)
			}
			absDir, err := filepath.Abs(args[0])
			if err != nil {
				return err
			}
			blockName, err := resolveBlockName(absDir, name)
			if err != nil {
				return err
			}
			return newProject(args[0], blockName, with)
		},
	}
	addNameFlag(cmd, &name)
	addWithFlag(cmd, &with)
	return cmd
}

// InitCmd returns the command that makes the current directory a block
// project, keeping the files already in it.
func InitCmd() *cobra.Command {
	var force bool
	var name string
	var with []string
	cmd := &cobra.Command{
		Use:   "init",
		Short: "Make the current directory a block project",
		Long: heredoc.Doc(`
			Make the current directory a block project. The name of the directory
			is used as the block name, unless --name is given.

			The directory may already hold files: files with the same name as a
			template file are kept and reported as skipped. If the directory already
			has a clay.yaml, clay init stops with an error. Use --force to overwrite
			existing files with the template; other files are always kept.

			clay init does not run in the filesystem root, the home folder, or the
			Desktop, Documents and Downloads folders in it, even with --force.

			Use --with to add optional files, as with clay new.
		`),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cwd, err := os.Getwd()
			if err != nil {
				return err
			}
			if err := ensureNotPersonalFolder(cwd); err != nil {
				return err
			}
			blockName, err := resolveBlockName(cwd, name)
			if err != nil {
				return err
			}
			err = bootstrap.CreateProject(cwd, blockName, force, with)
			if errors.Is(err, bootstrap.ErrProjectExists) {
				return fmt.Errorf("%w\nhint: use --force to overwrite its files with the template", err)
			}
			return err
		},
	}
	cmd.Flags().BoolVarP(&force, "force", "f", false, "overwrite existing files with the template")
	addNameFlag(cmd, &name)
	addWithFlag(cmd, &with)
	return cmd
}

func addWithFlag(cmd *cobra.Command, with *[]string) {
	cmd.Flags().StringSliceVar(with, "with", nil,
		"add optional files: "+strings.Join(bootstrap.Options, ", ")+" (repeat or separate with commas)")
}

func addNameFlag(cmd *cobra.Command, name *string) {
	cmd.Flags().StringVar(name, "name", "", "block name (default: the name of the project directory)")
}

func newProjectFromDeprecatedForm(cmd *cobra.Command, parentDir, blockName string, with []string) error {
	names, err := bname.Parse(blockName)
	if err != nil {
		return err
	}
	projectDir := filepath.Join(parentDir, names.Slug)
	replacementCommand := "clay new " + projectDir
	if slugLosesOriginalName := blockName != names.Slug; slugLosesOriginalName {
		replacementCommand += " --name " + blockName
	}
	fmt.Fprintf(cmd.ErrOrStderr(),
		"warning: 'clay new <path> <name>' is deprecated and will be removed in a future release; use '%s'\n",
		replacementCommand)
	return newProject(projectDir, blockName, with)
}

func newProject(projectDir, blockName string, with []string) error {
	entries, err := os.ReadDir(projectDir)
	if err != nil && !errors.Is(err, fs.ErrNotExist) {
		return err
	}
	if len(entries) > 0 {
		return fmt.Errorf("%s %w\nhint: to make it a block project, run 'clay init' in it", projectDir, errDirNotEmpty)
	}
	return bootstrap.CreateProject(projectDir, blockName, false, with)
}

func resolveBlockName(dir, nameFlag string) (string, error) {
	if nameFlag != "" {
		return nameFlag, nil
	}
	dirName := filepath.Base(dir)
	if _, err := bname.Parse(dirName); err != nil {
		return "", fmt.Errorf("directory name %q is not a valid block name; rename it or pass --name: %w", dirName, err)
	}
	return dirName, nil
}

func ensureNotPersonalFolder(dir string) error {
	refuse := func(folderDescription string) error {
		return fmt.Errorf("clay init does not use %s (%s): the project files would mix with your own files\n"+
			"hint: create the project in a new folder instead: clay new my-block", folderDescription, dir)
	}
	if isFilesystemRoot := filepath.Dir(dir) == dir; isFilesystemRoot {
		return refuse("the filesystem root")
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return nil
	}
	if isSameDir(dir, home) {
		return refuse("your home folder")
	}
	for _, folder := range personalHomeFolders {
		if isSameDir(dir, filepath.Join(home, folder)) {
			return refuse("your " + folder + " folder")
		}
	}
	return nil
}

func isSameDir(a, b string) bool {
	aInfo, aErr := os.Stat(a)
	bInfo, bErr := os.Stat(b)
	return aErr == nil && bErr == nil && os.SameFile(aInfo, bInfo)
}
