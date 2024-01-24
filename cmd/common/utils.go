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

type Url int

const (
	dev Url = iota
	stg
	prod
)

var EnvGateways = map[Url]string{
	dev:  "http://orchestrator.d.platform.example.com/",
	stg:  "http://orchestrator.platform-sandbox.example.com/",
	prod: "http://orchestrator.platform-staging.example.com/",
}

var S3bucket = map[Url]string{
	dev:  "d-platform-clay-public-catalog-s3-01",
	stg:  "s-platform-clay-public-catalog-s3-01",
	prod: "p-platform-clay-public-catalog-s3-01",
}

func (e Url) String() string {
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

func GetS3Bucket(env string) (s string) {

	switch env {
	case "dev":
		return S3bucket[dev]
	case "stg":
		return S3bucket[stg]
	case "prod":
		return S3bucket[prod]
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
