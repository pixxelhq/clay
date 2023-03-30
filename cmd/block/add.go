package block

import (
	"context"
	"fmt"

	"github.com/MakeNowJust/heredoc"
	"github.com/example/ramen/api/block"
	"github.com/example/ramen/pkg/logger"
	"github.com/spf13/cobra"
)

// addCmd represents the add command
var addCmd = &cobra.Command{
	Use:   "add [specFilePath]",
	Short: "Add a new block in Pixxel Labs ",
	Long: heredoc.Doc(`
    Add a new block in Pixxel Labs.
    A block, with the specification file, will be added to Pixxel Lab.
    It will be provided as a drag-and-drop feature to the users.`),
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.TODO()
		logger := getlogger()
		specFilePath := args[0]
		err := block.CreateNewBlock(ctx, logger, specFilePath)
		if err != nil {
			fmt.Println(err)
		}
		return err
	},
}

func getlogger() *logger.Logger {

	logger := logger.NewLogger(&logger.LogConfig{
		EnableConsoleLogging: true,
		LoggerName:           "ramen",
		ModuleName:           "ramen",
		Directory:            "/tmp/ramen/logs/",
		Filename:             "modelspec.logs.txt",
		MaxBackups:           0,
		MaxSize:              512,
		MaxAge:               0,
	})
	return logger
}

func init() {
	BlockCmd.AddCommand(addCmd)
}
