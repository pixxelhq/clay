package docker

import (
	"errors"
	"fmt"
	"os/exec"
)

var ErrDoesNotExists = errors.New("does not exist")

var ErrDaemonUnavailable = errors.New("cannot connect to the Docker daemon")

// CommandError is a command that exited with an error. errors.As on it gives
// the *exec.ExitError, and so the exit code.
type CommandError struct {
	Name string
	Hint string
	Err  *exec.ExitError
}

func (e *CommandError) Error() string {
	message := fmt.Sprintf("%s failed (exit %d)", e.Name, e.Err.ExitCode())
	if killedBySignal := e.Err.ExitCode() == -1; killedBySignal {
		message = fmt.Sprintf("%s was stopped (%s)", e.Name, e.Err)
	}
	if e.Hint != "" {
		message += "\nhint: " + e.Hint
	}
	return message
}

func (e *CommandError) Unwrap() error { return e.Err }
