package docker

import "errors"

var ErrDoesNotExists = errors.New("does not exist")

var ErrDaemonUnavailable = errors.New("cannot connect to the Docker daemon")
