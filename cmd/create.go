/*
Copyright © 2023 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"fmt"

	"github.com/example/ramen/pkg/bootstrap"
	"github.com/spf13/cobra"
)

// createCmd represents the create command
var createCmd = &cobra.Command{
	Use:   "create [outputDir] [modelName]",
	Short: "Generate a schema for your model",
	Long:  `Generate a schema for your model at outputDir`,

	Run: func(cmd *cobra.Command, args []string) {
		outputDir := args[0]
		modelName := args[1]
		err := bootstrap.CreateProject(outputDir, modelName)

		if err != nil {
			fmt.Println(err)
		}
	},
}

func init() {
	rootCmd.AddCommand(createCmd)

}
