package create

import (
	"github.com/MakeNowJust/heredoc"
	"github.com/spf13/cobra"
)

// addCmd represents the add command
var CreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Utility for project and dockerfile creation",
	Long:  heredoc.Doc(`Utility for project and dockerfile creation`),
}
