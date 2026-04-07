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
	describeCmdVersion string
)

func DescribeBlockCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "describe <name>",
		Short: "Describe the block for the given name",
		Long: heredoc.Doc(`
		If no flag provided, it will list all the versions of the given block name from clay registry.
		Use flag "version" to list a specific version of the block.
		Use flag "clay-registry-host" to list all the blocks from a specific registry.
		Example: clay list --version=0.0.1
		`),
		RunE: describeBlockCmd,
	}

	cmd.Flags().StringVarP(&describeCmdVersion, "version", "v", "", "Possible status of block: draft, released, disabled")
	return cmd
}

func describeBlockCmd(cmd *cobra.Command, args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("name argument is required")
	}
	name := args[0]

	br := registry.NewBlockRegistry(host, 5*time.Second)
	var (
		blocks registry.Blocks
		err    error
		block  *registry.Block
	)

	if describeCmdVersion != "" {
		block, err = br.GetBlockByNameAndVersion(name, describeCmdVersion)
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

	blocks, err = br.GetBlockByName(name)
	if err != nil {
		return err
	}

	for _, block := range blocks {
		prettyJSON, err := json.MarshalIndent(block, "", "  ")
		if err != nil {
			fmt.Printf("Failed to generate pretty JSON version %v, error : %s\n", block.Version, err)
			continue
		}
		fmt.Println(string(prettyJSON))
	}
	return nil
}
