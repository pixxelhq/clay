package cmd

import (
	"github.com/spf13/cobra"
)

var clayRegistryHost string

func BlockCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "block <command>",
		Short: "Manage blocks in the Clay registry",
		Long:  "List, describe, and manage assets for blocks in the Clay registry.",
	}

	cmd.AddCommand(ListBlockRegistryCmd())
	cmd.AddCommand(DescribeBlockCmd())
	cmd.AddCommand(BlockAssetsCmd())

	return cmd
}
