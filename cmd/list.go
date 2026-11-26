package cmd

import (
	"time"

	"github.com/MakeNowJust/heredoc"
	"github.com/pixxelhq/clay/pkg/registry"
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
		RunE:    listBlockRegistryCmd,
	}

	cmd.Flags().StringVar(&clayRegistryHost, "clay-registry", "", "Clay block registry URL (required)")
	cmd.Flags().StringVarP(&name, "name", "n", "", "Name of block")
	cmd.Flags().StringVarP(&version, "version", "v", "", "Version of the block")
	return cmd
}

func listBlockRegistryCmd(_ *cobra.Command, _ []string) error {
	r := registry.New(clayRegistryHost, 5*time.Second)

	if name != "" && version != "" {
		block, err := r.GetBlockByNameAndVersion(name, version)
		if err != nil {
			return err
		}
		return writePrettyJSON(block)
	}

	var (
		blocks registry.Blocks
		err    error
	)
	if name != "" {
		blocks, err = r.GetBlockByName(name)
	} else {
		blocks, err = r.ListBlocks()
	}
	if err != nil {
		return err
	}

	return writePrettyJSON(blocks)
}
