/*
Copyright © 2023 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"fmt"

	"github.com/example/ramen/pkg/bootstrap"
	"github.com/example/ramen/pkg/dockerfile"
	"github.com/spf13/cobra"
)

var useHttpRunner bool

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

var dockerCmd = &cobra.Command{
	Use:   "create-dockerfile [modelSpecificationPath] [sourceCodeFolder] [useHttpRunner]",
	Short: "Creates a dockerfile to package and serve your model",
	Long: `
	Creates a dockerfile using your model spec assuming that sourceCodeFolder contains all the necessray code.
	Set the http Flag to create a dockerfile that runs the model as a server instead of a job.
	`,

	Run: func(cmd *cobra.Command, args []string) {
		modelSpecificationPath := args[0]
		sourceCodeFolder := args[1]
		err := dockerfile.GenerateDockerfile(modelSpecificationPath, sourceCodeFolder, useHttpRunner)

		if err != nil {
			fmt.Println(err)
		}
	},
}

func init() {
	dockerCmd.Flags().BoolVar(&useHttpRunner, "http", false, "Set flag to package model as an http server instead of a job")
	rootCmd.AddCommand(dockerCmd)
	rootCmd.AddCommand(createCmd)
}
