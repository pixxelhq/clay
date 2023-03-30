package bootstrap

import (
	"testing"
)

// TODO: Write a much better and more comprehensive test
func TestBootstrap(t *testing.T) {
	outDir := "sample_project"
	modelName := "AwesomeModel"
	defer deleteDir(outDir)
	err := CreateProject(outDir, modelName)
	if err != nil {
		t.Errorf("Test failed: %s", err.Error())
	}
}
