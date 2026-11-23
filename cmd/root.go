package cmd

import (
	"fmt"
	"os"

	"github.com/MakeNowJust/heredoc"
	newproject "github.com/pixxelhq/clay/cmd/newproject"
	"github.com/spf13/cobra"
)

// RootCmd represents the base command when called without any subcommands
var RootCmd = &cobra.Command{
	Use:           "clay",
	SilenceUsage:  true,
	SilenceErrors: true,
	Short:         "A tool to bridge gap between block development on local machines and deployment on the platform",
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
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
}

func init() {
	RootCmd.SetFlagErrorFunc(func(cmd *cobra.Command, err error) error {
		return fmt.Errorf("%w\nhint: run '%s --help' to see the flags", err, cmd.CommandPath())
	})
	RootCmd.AddCommand(newproject.NewCmd())
	RootCmd.AddCommand(newproject.InitCmd())
	RootCmd.AddCommand(VersionCmd())
	RootCmd.AddCommand(buildDockerImageCmd())
	RootCmd.AddCommand(printDockerfileCmd())
	RootCmd.AddCommand(pushToDockerRegistryCmd())
	RootCmd.AddCommand(runDockerImageCmd())
	RootCmd.AddCommand(publishBlockToRegistryCmd())
	RootCmd.AddCommand(BlockCmd())
	addHelpHintToArgErrors(RootCmd)
}

func addHelpHintToArgErrors(cmd *cobra.Command) {
	if validateArgs := cmd.Args; validateArgs != nil {
		cmd.Args = func(c *cobra.Command, args []string) error {
			if err := validateArgs(c, args); err != nil {
				return fmt.Errorf("%w\nhint: run '%s --help' to see its arguments", err, c.CommandPath())
			}
			return nil
		}
	}
	for _, sub := range cmd.Commands() {
		addHelpHintToArgErrors(sub)
	}
}
