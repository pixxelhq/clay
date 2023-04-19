package block

import (
	"context"
	"errors"
	"os"

	"github.com/MakeNowJust/heredoc"
	"github.com/example/clay/api/block"
	"github.com/example/clay/pkg/logger"
	"github.com/spf13/cobra"
)

// addCmd represents the add command
var addCmd = &cobra.Command{
	Use:   "add [specFilePath] [email] [password]",
	Short: "Add a new block in Pixxel Labs ",
	Long: heredoc.Doc(`
    Add a new block in Pixxel Labs.
    A block, with the specification file, will be added to Pixxel Lab.
    It will be provided as a drag-and-drop feature to the users.
	Provide the login credentials registered with "auth.example.com"`),
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.TODO()
		logger := getlogger()
		var (
			specFilePath string
			username     string
			password     string
		)

		if len(os.Args) < 6 {
			return (errors.New("provide [specFilePath] [email] [password] as arguments"))
		} else {
			specFilePath = args[0]
			username = args[1]
			password = args[2]
		}

		err := block.PostNewBlock(ctx, logger, specFilePath, username, password)
		if err != nil {
			return err
		}
		return nil
	},
}

func getlogger() *logger.Logger {

	logger := logger.NewLogger(&logger.LogConfig{
		EnableConsoleLogging: true,
		LoggerName:           "clay",
		ModuleName:           "clay",
		Directory:            "/tmp/clay/logs/",
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
