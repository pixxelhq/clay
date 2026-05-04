package cmd

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/MakeNowJust/heredoc"
	"github.com/pixxelhq/clay-framework/pkg/registry"
	"github.com/spf13/cobra"
)

var (
	name    string
	version string
)

func ListBlockRegistryCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List blocks in the Clay registry",
		Long: heredoc.Doc(`
		List blocks from the Clay registry.
		If no flags are provided, it will list all the latest blocks.
		Use --name to list all versions of a specific block.
		Use --name with --version to list a specific version.
		`),
		Example: "clay block list --name=my-block --version=0.0.1",
		RunE: listBlockRegistryCmd,
	}

	cmd.Flags().StringVar(&clayRegistryHost, "clay-registry", "", "Clay block registry URL (env: CLAY_REGISTRY_HOST)")
	cmd.Flags().StringVarP(&name, "name", "n", "", "Name of block")
	cmd.Flags().StringVarP(&version, "version", "v", "", "Version of the block")
	return cmd
}

func listBlockRegistryCmd(cmd *cobra.Command, args []string) error {
	r := registry.New(clayRegistryHost, 5*time.Second)
	var (
		blocks registry.Blocks
		err    error
		block  *registry.Block
	)

	if name != "" && version != "" {
		block, err = r.GetBlockByNameAndVersion(name, version)
		if err != nil {
			return err
		}

		prettyJSON, err := json.MarshalIndent(block, "", "  ")
		if err != nil {
			fmt.Printf("Failed to generate pretty JSON: %s\n", err)
		}

		fmt.Println(string(prettyJSON))
		return nil
	}

	if name != "" {
		blocks, err = r.GetBlockByName(name)
		if err != nil {
			return err
		}

	} else {
		blocks, err = r.ListBlocks()
		if err != nil {
			return err
		}

	}

	for _, block := range blocks {
		prettyJSON, err := json.MarshalIndent(block, "", "  ")
		if err != nil {
			fmt.Printf("Failed to generate pretty JSON: %s\n", err)
			continue
		}
		fmt.Println(string(prettyJSON))
	}
	return nil
}
