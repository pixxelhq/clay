package cmd

import (
	"github.com/spf13/cobra"
	
	"github.com/example/clay/cmd/marketplace"
)

func UploadCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "upload",
		Short: "Upload marketplace artifacts to cloud store",
	}

	cmd.AddCommand(marketplace.UploadReadme())
	return cmd
}
