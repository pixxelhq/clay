package common

import (
	"github.com/example/clay/pkg/logger"
	"golang.org/x/mod/semver"
)

func IsValidVersion(version string) bool {
	if semver.IsValid(version) {
		return true
	} else {
		return false
	}

}

func Getlogger() *logger.Logger {

	logger := logger.NewLogger(&logger.LogConfig{
		EnableConsoleLogging: true,
		LoggerName:           "clay",
		ModuleName:           "clay",
		Directory:            "/tmp/clay/logs/",
		Filename:             "blockspec.logs.txt",
		MaxBackups:           0,
		MaxSize:              512,
		MaxAge:               0,
	})
	return logger
}

type UnauthorisedError struct {
	Msg string
}

func (u UnauthorisedError) Error() string {
	return u.Msg
}

func NewUnauthorisedError(msg string) error {
	return UnauthorisedError{msg}
}
