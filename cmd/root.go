package cmd

import (
	"os"

	"github.com/MakeNowJust/heredoc"
	"github.com/example/clay/cmd/create"
	"github.com/spf13/cobra"
)

// RootCmd represents the base command when called without any subcommands
var RootCmd = &cobra.Command{
	Use:          "clay",
	SilenceUsage: true,
	Short:        "A tool to bridge gap between model development on local machines and deployment on the platform",
	Long: heredoc.Doc(`Clay provide users the tooling and the scaffolding needed to quickly:
	1.Refactor their model in a pre-defined structure
	2.Programmatically declare their inputs and outputs, environment and compute requirements
	3.Provide tooling to easily and locally test their models that are deployed on our infra`),
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the RootCmd.
func Execute() {
	err := RootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {

	RootCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
	RootCmd.PersistentFlags().StringP("env", "e", "dev", "Environment to add new block to: dev, stg, prod")
	RootCmd.AddCommand(create.CreateCmd)
	RootCmd.AddCommand(VersionCmd())
	RootCmd.AddCommand(GetCmd())
	RootCmd.AddCommand(ListCmd())
	RootCmd.AddCommand(AddNewCmd())
	RootCmd.AddCommand(UpdateCmd())
	RootCmd.AddCommand(UploadCmd())
	RootCmd.AddCommand(buildDockerImageCmd())
	RootCmd.AddCommand(pushToDockerRegistryCmd())
	RootCmd.AddCommand(publishModelToRegistryCmd())
	RootCmd.AddCommand(BlockCmd())
}
