package block

import (
	"github.com/MakeNowJust/heredoc"
	"github.com/spf13/cobra"
)

// addCmd represents the add command
var BlockCmd = &cobra.Command{
	Use:   "block",
	Short: "Block Related Operations",
	Long:  heredoc.Doc(`Block Related Operations`),
}
