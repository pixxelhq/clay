package cmd

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/MakeNowJust/heredoc"
	"github.com/example/clay/cmd/block"
	"github.com/example/clay/pkg/registry"
	"github.com/spf13/cobra"
)

var (
	host    string
	name    string
	version string
)

func ListCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list <command>",
		Short: "List block, workflows",
	}

	cmd.AddCommand(block.ListBlockCmd())
	return cmd
}

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

	// cmd.Flags().StringVarP(&host, "model-registry-host", "crh", "http://clay-registry-staging.example.com", "model registry host")
	cmd.Flags().StringVarP(&name, "name", "n", "", "Name of block")
	cmd.Flags().StringVarP(&version, "version", "v", "", "Possible status of block: draft, released, disabled")
	cmd.Flags().StringVarP(&host, "host", "", "https://clay-registry.example.com", "Possible status of block: draft, released, disabled")
	return cmd
}

func listBlockRegistryCmd(cmd *cobra.Command, args []string) error {
	mr := registry.NewModelRegistry(host, 5*time.Second)
	var (
		models registry.Models
		err    error
		model  *registry.Model
	)

	if name != "" && version != "" {
		model, err = mr.GetBlockByNameAndVersion(name, version)
		if err != nil {
			return err
		}

		prettyJSON, err := json.MarshalIndent(model, "", "  ")
		if err != nil {
			fmt.Printf("Failed to generate pretty JSON: %s\n", err)
		}

		fmt.Println(string(prettyJSON))
		return nil
	}

	if name != "" {
		models, err = mr.GetBlockByName(name)
		if err != nil {
			return err
		}

	} else {
		models, err = mr.ListBlocks()
		if err != nil {
			return err
		}

	}

	for _, model := range models {
		prettyJSON, err := json.MarshalIndent(model, "", "  ")
		if err != nil {
			fmt.Printf("Failed to generate pretty JSON: %s\n", err)
			continue
		}
		fmt.Println(string(prettyJSON))
	}
	return nil
}
