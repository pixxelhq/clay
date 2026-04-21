package main

import (
	_ "embed"
	"regexp"

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
	Version := match[1]
	docker.ClayVersion = Version
	cmd.Version = Version
}
