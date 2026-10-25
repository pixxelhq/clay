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

// NewCmd scaffolds a new block project at the given path.
var NewCmd = &cobra.Command{
	Use:   "new <path> <name>",
	Short: "Scaffold a new block project",
	Long: heredoc.Doc(`
		Scaffold a new block project at the given path.

		<path> is the output directory where the project files will be created.
		<name> is the block name, used in clay.yaml and module scaffolding.

		If the project directory already exists and is not empty, clay new stops
		with an error. Use --force to write the template files into it anyway;
		files that are not part of the template are kept.
	`),
	Example: "clay new ./my-block weather-forecaster",
	Args:    cobra.ExactArgs(2),
	RunE: func(cmd *cobra.Command, args []string) error {
		outputDir := args[0]
		blockName := args[1]
		force, _ := cmd.Flags().GetBool("force")
		err := bootstrap.CreateProject(outputDir, blockName, force)
		if errors.Is(err, bootstrap.ErrProjectDirNotEmpty) {
			return fmt.Errorf("%w\nhint: use --force to write the template into it anyway", err)
		}
		return err
	},
}

func init() {
	NewCmd.Flags().BoolP("force", "f", false, "write the template into an existing non-empty directory")
}
