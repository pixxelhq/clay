package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

var Version string

func VersionCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "version",
		Short: "Print the Clay CLI and SDK version",
		Long:  "Print the current Clay version. The CLI and Python SDK share the same version.",
		RunE: func(cmd *cobra.Command, args []string) error {
			if Version == "" {
				fmt.Println("Version information not available.")
				return nil
			}

			fmt.Printf("clay version %s\n", Version)
			return nil
		},
	}
}
