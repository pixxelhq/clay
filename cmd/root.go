package cmd

import (
	"os"

	"github.com/MakeNowJust/heredoc"
	newproject "github.com/pixxelhq/clay/cmd/newproject"
	"github.com/spf13/cobra"
)

// RootCmd represents the base command when called without any subcommands
var RootCmd = &cobra.Command{
	Use:          "clay",
	SilenceUsage: true,
	Short:        "A tool to bridge gap between block development on local machines and deployment on the platform",
	Long: heredoc.Doc(`Clay provides the tooling and scaffolding needed to quickly:
	1. Refactor your block into a pre-defined structure
	2. Programmatically declare inputs, outputs, environment and compute requirements
	3. Easily build, test and deploy your blocks locally or on your infrastructure`),
	CompletionOptions: cobra.CompletionOptions{
		DisableDefaultCmd: true,
	},
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the RootCmd.
func Execute() {
	RootCmd.Version = Version
	err := RootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {
	RootCmd.AddCommand(newproject.NewCmd)
	RootCmd.AddCommand(VersionCmd())
	RootCmd.AddCommand(buildDockerImageCmd())
	RootCmd.AddCommand(pushToDockerRegistryCmd())
	RootCmd.AddCommand(runDockerImageCmd())
	RootCmd.AddCommand(publishBlockToRegistryCmd())
	RootCmd.AddCommand(BlockCmd())
}
