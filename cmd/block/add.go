package block

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"syscall"

	"github.com/MakeNowJust/heredoc"
	"github.com/example/clay/api/block"
	"github.com/example/clay/pkg/logger"
	"github.com/spf13/cobra"
	"golang.org/x/term"
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
		specFilePath := args[0]

		reader := bufio.NewReader(os.Stdin)

		fmt.Print("Enter email: ")
		username, err := reader.ReadString('\n')
		if err != nil {
			return err
		}

		fmt.Print("Enter Password: ")
		bytePassword, err := term.ReadPassword(int(syscall.Stdin))
		if err != nil {
			return err
		}
		password := string(bytePassword)

		err = block.PostNewBlock(ctx, logger, specFilePath, username, password)
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
