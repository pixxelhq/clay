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
		Describe the block for the given name from the Clay registry.
		If no version flag is provided, it will list all versions of the given block.
		Use --version to describe a specific version of the block.
		`),
		Example: "clay block describe my-block --version=0.0.1",
		Args:    cobra.ExactArgs(1),
		RunE:    describeBlockCmd,
	}
	cmd.Flags().StringVar(&clayRegistryHost, "clay-registry", "", "Clay block registry URL (env: CLAY_REGISTRY_HOST)")
	cmd.Flags().StringVarP(&describeCmdVersion, "version", "v", "", "Possible status of block: draft, released, disabled")
	return cmd
}

func describeBlockCmd(cmd *cobra.Command, args []string) error {
	name := args[0]

	r := registry.New(clayRegistryHost, 5*time.Second)
	var (
		blocks registry.Blocks
		err    error
		block  *registry.Block
	)

	if describeCmdVersion != "" {
		block, err = r.GetBlockByNameAndVersion(name, describeCmdVersion)
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

	blocks, err = r.GetBlockByName(name)
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
