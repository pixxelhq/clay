package cmd

import (
	"github.com/example/clay/cmd/marketplace"
	"github.com/spf13/cobra"
)

func UploadCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "upload",
		Short: "Upload marketplace artifacts to cloud store",
	}

	cmd.AddCommand(marketplace.UploadReadme())
	return cmd
}
