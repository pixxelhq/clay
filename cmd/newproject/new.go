// Package newproject implements the `clay new` and `clay init` commands,
// which scaffold a new block project. The package is named "newproject"
// (not "new") to avoid clashing with Go's built-in new() function.
package newproject

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"

	"github.com/MakeNowJust/heredoc"
	"github.com/pixxelhq/clay/api/bootstrap"
	"github.com/pixxelhq/clay/pkg/blockname"
	"github.com/spf13/cobra"
)

// NewCmd returns the command that scaffolds a new block project in the
// given directory.
func NewCmd() *cobra.Command {
	var force bool
	cmd := &cobra.Command{
		Use:   "new <path>",
		Short: "Scaffold a new block project",
		Long: heredoc.Doc(`
			Scaffold a new block project in the directory <path>. The last part of
			the path is used as the block name.

			The block name is letters, digits, '-' and '_'. my-block, my_block and
			MyBlock all give:

			  clay.yaml name and image   my-block
			  Python package folder      my_block
			  Python class               MyBlock

			If the directory is not empty, clay new stops with an error. Use --force
			to write the template files into it anyway; files that are not part of
			the template are kept.
		`),
		Example: heredoc.Doc(`
			clay new my-block                # creates ./my-block
			clay new ~/blocks/weather-model  # creates ~/blocks/weather-model
		`),
		Args: cobra.RangeArgs(1, 2),
		RunE: func(cmd *cobra.Command, args []string) error {
			projectDir := args[0]
			absDir, err := filepath.Abs(projectDir)
			if err != nil {
				return err
			}
			blockName := filepath.Base(absDir)
			if len(args) == 2 {
				// deprecated form: clay new <parent-dir> <name>
				names, err := blockname.Parse(args[1])
				if err != nil {
					return err
				}
				blockName = args[1]
				projectDir = filepath.Join(args[0], names.Slug)
				fmt.Fprintf(cmd.ErrOrStderr(),
					"warning: 'clay new <path> <name>' is deprecated and will be removed in a future release; use 'clay new %s'\n",
					projectDir)
			}
			return createProject(projectDir, blockName, force)
		},
	}
	addForceFlag(cmd, &force)
	return cmd
}

// InitCmd returns the command that scaffolds a new block project in the
// current directory.
func InitCmd() *cobra.Command {
	var force bool
	cmd := &cobra.Command{
		Use:   "init",
		Short: "Scaffold a new block project in the current directory",
		Long: heredoc.Doc(`
			Scaffold a new block project in the current directory. The name of the
			directory is used as the block name.

			If the directory is not empty, clay init stops with an error. Use --force
			to write the template files into it anyway; files that are not part of
			the template are kept.
		`),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cwd, err := os.Getwd()
			if err != nil {
				return err
			}
			return createProject(cwd, filepath.Base(cwd), force)
		},
	}
	addForceFlag(cmd, &force)
	return cmd
}

func addForceFlag(cmd *cobra.Command, force *bool) {
	cmd.Flags().BoolVarP(force, "force", "f", false, "write the template into an existing non-empty directory")
}

func createProject(projectDir, blockName string, force bool) error {
	err := bootstrap.CreateProject(projectDir, blockName, force)
	if errors.Is(err, bootstrap.ErrProjectDirNotEmpty) {
		return fmt.Errorf("%w\nhint: use --force to write the template into it anyway", err)
	}
	return err
}
