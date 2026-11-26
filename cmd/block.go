package cmd

import (
	"encoding/json"
	"fmt"

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

func writePrettyJSON(v any) error {
	prettyJSON, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to generate pretty JSON: %w", err)
	}
	_, err = fmt.Println(string(prettyJSON))
	return err
}
