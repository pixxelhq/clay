package main

import (
	_ "embed"
	"fmt"
	"regexp"

	"github.com/example/clay/api/bootstrap"
	"github.com/example/clay/api/dockerfile"
	"github.com/example/clay/cmd"
)

//go:embed python/clay/__version__.py
var versionString string

func main() {
	Version := getSetVersion()
	fmt.Println("Version:", Version)
	fmt.Println()
	cmd.Execute()
}

func getSetVersion() string {
	re := regexp.MustCompile(`"([^"]*)"`)
	match := re.FindStringSubmatch(versionString)
	Version := match[1]
	bootstrap.Version = Version
	dockerfile.Version = Version
	return Version
}
