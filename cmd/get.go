package cmd

import (
	"github.com/example/clay/cmd/block"
	"github.com/spf13/cobra"
)

func GetCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get <block>",
		Short: "Get blocks, Workflows",
	}

	cmd.AddCommand(block.GetBlockCmd())
	return cmd
}
