package main

import (
	_ "embed"
	"regexp"

	"github.com/pixxelhq/clay-framework/cmd"
	"github.com/pixxelhq/clay-framework/pkg/docker"
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
