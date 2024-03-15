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
	Short: "Generate starter files for your model",
	Long:  heredoc.Doc(`Generate starter files for your model`),

	RunE: func(cmd *cobra.Command, args []string) error {
		if len(args) < 2 {
			return fmt.Errorf("invalid argument to the command please check `clay create project --help`")
		}
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
