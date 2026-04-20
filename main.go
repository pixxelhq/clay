package main

import (
	_ "embed"
	"regexp"

	"github.com/example/clay/api/bootstrap"
	"github.com/example/clay/cmd"
	"github.com/example/clay/pkg/docker"
)

//go:embed python/clay/__version__.py
var versionString string

func main() {
	getSetVersion()
	cmd.Execute()
}

func getSetVersion() {
	re := regexp.MustCompile(`"([^"]*)"`)
	match := re.FindStringSubmatch(versionString)
	version := match[1]
	cmd.Version = version
	bootstrap.Version = version
	docker.ClayVersion = version
}
