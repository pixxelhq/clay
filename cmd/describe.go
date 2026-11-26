package cmd

import (
	"time"

	"github.com/MakeNowJust/heredoc"
	"github.com/pixxelhq/clay/pkg/registry"
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
	cmd.Flags().StringVar(&clayRegistryHost, "clay-registry", "", "Clay block registry URL (required)")
	cmd.Flags().StringVarP(&describeCmdVersion, "version", "v", "", "Specific version to describe (omit to list all versions)")
	return cmd
}

func describeBlockCmd(_ *cobra.Command, args []string) error {
	blockName := args[0]

	r := registry.New(clayRegistryHost, 5*time.Second)

	if describeCmdVersion != "" {
		block, err := r.GetBlockByNameAndVersion(blockName, describeCmdVersion)
		if err != nil {
			return err
		}
		return writePrettyJSON(block)
	}

	blocks, err := r.GetBlockByName(blockName)
	if err != nil {
		return err
	}

	return writePrettyJSON(blocks)
}
