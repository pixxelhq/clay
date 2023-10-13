package common

import (
	"errors"
	"os"

	"github.com/example/clay/pkg/logger"
	"golang.org/x/mod/semver"
)

const (
	UsernameEnvVar = "AURORA_USERNAME"
	PasswordEnvVar = "AURORA_PASSWORD"
)

type Credentials struct {
	Username string
	Password string
}

var ErrMissingCredentials = errors.New("set AURORA_USERNAME and AURORA_PASSWORD as env variable")

func GetCredentials() (Credentials, error) {

	username := os.Getenv(UsernameEnvVar)
	password := os.Getenv(PasswordEnvVar)
	if (username == "") || (password == "") {
		return Credentials{}, ErrMissingCredentials
	}
	creds := Credentials{
		Username: username,
		Password: password,
	}

	return creds, nil
}

func IsValidVersion(version string) bool {
	if semver.IsValid(version) {
		return true
	} else {
		return false
	}

}

type EnvUrl int

const (
	dev EnvUrl = iota
	stg
	prod
)

var EnvGateways = map[EnvUrl]string{
	dev:  "https://platform-gateway.example.com/orchestrator/",
	stg:  "https://s-platform-gateway.example.com/orchestrator/",
	prod: "https://p-platform-gateway.example.com/orchestrator/",
}

func (e EnvUrl) String() string {
	return [...]string{"dev", "stg", "prod"}[e]
}

func GetUrl(env string) (s string) {

	switch env {
	case "dev":
		return EnvGateways[dev]
	case "stg":
		return EnvGateways[stg]
	case "prod":
		return EnvGateways[prod]
	default:
		return ""
	}
}

func Getlogger() *logger.Logger {

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

type UnauthorisedError struct {
	Msg string
}

func (u UnauthorisedError) Error() string {
	return u.Msg
}

func NewUnauthorisedError(msg string) error {
	return UnauthorisedError{msg}
}
