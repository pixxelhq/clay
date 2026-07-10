// Package newproject implements the `clay new` command, which scaffolds
// a new block project. The package is named "newproject" (not "new") to
// avoid clashing with Go's built-in new() function.
package newproject

import (
	"fmt"

	"github.com/MakeNowJust/heredoc"
	"github.com/pixxelhq/clay-framework/api/bootstrap"
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
	`),
	Example: "clay new ./my-block weather-forecaster",
	Args:    cobra.ExactArgs(2),
	RunE: func(cmd *cobra.Command, args []string) error {
		outputDir := args[0]
		blockName := args[1]
		err := bootstrap.CreateProject(outputDir, blockName)
		if err != nil {
			fmt.Println(err)
		}
		return err
	},
}
