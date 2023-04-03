package create

import (
	"fmt"

	"github.com/MakeNowJust/heredoc"
	"github.com/example/clay/api/dockerfile"
	"github.com/spf13/cobra"
)

var useHttpRunner bool

// Creates a dockerfile for packaging a model
var dockerCmd = &cobra.Command{
	Use:   "dockerfile [modelSpecificationPath] [sourceCodeFolder] [useHttpRunner]",
	Short: "Creates a dockerfile to package and serve your model",
	Long: heredoc.Doc(`
	Creates a dockerfile using your model spec assuming that sourceCodeFolder contains all the necessray code.
	Set the http Flag to create a dockerfile that runs the model as a server instead of a job.
	`),

	RunE: func(cmd *cobra.Command, args []string) error {
		modelSpecificationPath := args[0]
		sourceCodeFolder := args[1]
		err := dockerfile.GenerateDockerfile(modelSpecificationPath, sourceCodeFolder, useHttpRunner)
		if err != nil {
			fmt.Println(err)
		}
		return err
	},
}

func init() {
	dockerCmd.Flags().BoolVar(&useHttpRunner, "http", false, "Set flag to package model as an http server instead of a job")
	CreateCmd.AddCommand(dockerCmd)
}
