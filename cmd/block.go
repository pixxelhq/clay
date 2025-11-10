package cmd

import (
	"github.com/spf13/cobra"
)

var host string

func BlockCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "block <command>",
		Short: "block commands",
	}

	cmd.PersistentFlags().StringVarP(&host, "host", "", "https://clay-registry.example.com", "Host of the clay registry where you models are published")
	cmd.AddCommand(ListBlockRegistryCmd())
	cmd.AddCommand(DescribeBlockCmd())
	cmd.AddCommand(BlockAssetsCmd())

	return cmd
}
