package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var clayRegistryHost string

func BlockCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "block <command>",
		Short: "Manage blocks in the Clay registry",
		Long:  "List, describe, and manage assets for blocks in the Clay registry.",
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
			if clayRegistryHost == "" {
				if clayRegistryHost = os.Getenv("CLAY_REGISTRY_HOST"); clayRegistryHost == "" {
					return fmt.Errorf("--clay-registry is required (or set CLAY_REGISTRY_HOST env var)")
				}
			}
			return nil
		},
	}

	cmd.AddCommand(ListBlockRegistryCmd())
	cmd.AddCommand(DescribeBlockCmd())
	cmd.AddCommand(BlockAssetsCmd())

	return cmd
}
