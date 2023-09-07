package cmd

import (
	"github.com/example/clay/cmd/block"
	"github.com/spf13/cobra"
)

func AddNewCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "add <command>",
		Short: "Add new blocks, Workflows",
	}

	cmd.AddCommand(block.AddBlockCmd())
	return cmd
}
