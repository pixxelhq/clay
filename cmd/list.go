package cmd

import (
	"github.com/example/clay/cmd/block"
	"github.com/spf13/cobra"
)

func ListCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list <command>",
		Short: "List block, workflows",
	}

	cmd.AddCommand(block.ListBlockCmd())
	return cmd
}
