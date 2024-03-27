package main

import (
	_ "embed"
	"regexp"

	"github.com/example/clay/api/bootstrap"
	"github.com/example/clay/api/dockerfile"
	"github.com/example/clay/cmd"
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
	bootstrap.Version = Version
	dockerfile.Version = Version
}
