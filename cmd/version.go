package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

var Version string

func VersionCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "version",
		Short: "Get clay cli version",
		RunE: func(cmd *cobra.Command, args []string) error {
			if Version == "" {
				fmt.Println("Version information not available.")
				return nil
			}

			fmt.Println(Version)
			return nil
		},
	}
}
