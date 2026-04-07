package cmd

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/MakeNowJust/heredoc"
	"github.com/example/clay/pkg/registry"
	"github.com/spf13/cobra"
)

var (
	name    string
	version string
)

func ListBlockRegistryCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List block",
		Long: heredoc.Doc(`
		If no flag provided, it will list all the latest block from clay registry
		Use flag "name" to list all the versions of the block.
		Use flag "version" after "name" to list a specific version of the block.
		Use flag "clay-registry-host" to list all the blocks from a specific registry.
		Example: clay list --name=block-name --version=0.0.1
		`),
		RunE: listBlockRegistryCmd,
	}

	cmd.Flags().StringVarP(&name, "name", "n", "", "Name of block")
	cmd.Flags().StringVarP(&version, "version", "v", "", "Version of the block")
	return cmd
}

func listBlockRegistryCmd(cmd *cobra.Command, args []string) error {
	br := registry.NewBlockRegistry(host, 5*time.Second)
	var (
		blocks registry.Blocks
		err    error
		block  *registry.Block
	)

	if name != "" && version != "" {
		block, err = br.GetBlockByNameAndVersion(name, version)
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
		blocks, err = br.GetBlockByName(name)
		if err != nil {
			return err
		}

	} else {
		blocks, err = br.ListBlocks()
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
