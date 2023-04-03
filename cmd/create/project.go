package create

import (
	"fmt"

	"github.com/MakeNowJust/heredoc"
	"github.com/example/clay/api/bootstrap"
	"github.com/spf13/cobra"
)

// createCmd represents the create command
var projectCmd = &cobra.Command{
	Use:   "project [outputDir] [modelName]",
	Short: "Generate a schema for your model",
	Long:  heredoc.Doc(`Generate a schema for your model at outputDir`),

	RunE: func(cmd *cobra.Command, args []string) error {
		outputDir := args[0]
		modelName := args[1]
		err := bootstrap.CreateProject(outputDir, modelName)
		if err != nil {
			fmt.Println(err)
		}
		return err
	},
}

func init() {
	CreateCmd.AddCommand(projectCmd)
}
