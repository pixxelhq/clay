package cmd

import (
	"github.com/example/clay/cmd/block"
	"github.com/spf13/cobra"
)

func UpdateCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "update <command>",
		Short: "Update existing blocks, Workflows",
	}

	cmd.AddCommand(block.UpdateBlockCmd())
	return cmd
}
