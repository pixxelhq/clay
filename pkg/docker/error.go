package docker

import "errors"

var ErrDoesNotExists = errors.New("does not exists")

var ErrDaemonUnavailable = errors.New("cannot connect to the Docker daemon")
