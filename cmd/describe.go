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

	mr := registry.NewModelRegistry(host, 5*time.Second)
	var (
		models registry.Models
		err    error
		model  *registry.Model
	)

	if describeCmdVersion != "" {
		model, err = mr.GetBlockByNameAndVersion(name, describeCmdVersion)
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

	models, err = mr.GetBlockByName(name)
	if err != nil {
		return err
	}

	for _, model := range models {
		prettyJSON, err := json.MarshalIndent(model, "", "  ")
		if err != nil {
			fmt.Printf("Failed to generate pretty JSON version %v, error : %s\n", model.Version, err)
			continue
		}
		fmt.Println(string(prettyJSON))
	}
	return nil
}
