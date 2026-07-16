package common

import (
	"github.com/pixxelhq/clay/pkg/logger"
	"golang.org/x/mod/semver"
)

func IsValidVersion(version string) bool {
	return semver.IsValid(version)
}

func Getlogger() *logger.Logger {
	return logger.NewLogger(&logger.LogConfig{
		EnableConsoleLogging: true,
		LoggerName:           "clay",
		ModuleName:           "clay",
		Directory:            "/tmp/clay/logs/",
		Filename:             "blockspec.logs.txt",
		MaxBackups:           0,
		MaxSize:              512,
		MaxAge:               0,
	})
}
