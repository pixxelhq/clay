package bootstrap

import (
	"testing"
)

// TODO: Write a much better and more comprehensive test
func TestBootstrap(t *testing.T) {
	outDir := "sample_project"
	blockName := "AwesomeBlock"
	defer deleteDir(outDir)
	err := CreateProject(outDir, blockName)
	if err != nil {
		t.Errorf("Test failed: %s", err.Error())
	}
}