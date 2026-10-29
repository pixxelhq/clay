// Package newproject implements the `clay new` command, which scaffolds
// a new block project. The package is named "newproject" (not "new") to
// avoid clashing with Go's built-in new() function.
package newproject

import (
	"errors"
	"fmt"

	"github.com/MakeNowJust/heredoc"
	"github.com/pixxelhq/clay/api/bootstrap"
	"github.com/spf13/cobra"
)

// NewCmd returns the command that scaffolds a new block project at the
// given path.
func NewCmd() *cobra.Command {
	var force bool
	cmd := &cobra.Command{
		Use:   "new <path> <name>",
		Short: "Scaffold a new block project",
		Long: heredoc.Doc(`
			Scaffold a new block project at the given path.

			<path> is the output directory where the project files will be created.
			<name> is the block name: letters, digits, '-' and '_'. my-block, my_block
			and MyBlock all give:

			  clay.yaml name, image, project folder   my-block
			  Python package folder                   my_block
			  Python class                            MyBlock

			If the project directory already exists and is not empty, clay new stops
			with an error. Use --force to write the template files into it anyway;
			files that are not part of the template are kept.
		`),
		Example: "clay new ./my-block weather-forecaster",
		Args:    cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			outputDir := args[0]
			blockName := args[1]
			err := bootstrap.CreateProject(outputDir, blockName, force)
			if errors.Is(err, bootstrap.ErrProjectDirNotEmpty) {
				return fmt.Errorf("%w\nhint: use --force to write the template into it anyway", err)
			}
			return err
		},
	}
	cmd.Flags().BoolVarP(&force, "force", "f", false, "write the template into an existing non-empty directory")
	return cmd
}
