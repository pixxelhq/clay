package cmd

import (
	"github.com/spf13/cobra"
)

func BlockCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "block <command>",
		Short: "block commands",
	}

	cmd.AddCommand(ListBlockRegistryCmd())
	return cmd
}
