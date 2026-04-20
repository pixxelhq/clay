package bootstrap

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TODO: Write a much better and more comprehensive test
func TestBootstrap(t *testing.T) {
	outDir := "sample_project"
	blockName := "AwesomeBlock"
	defer deleteDir(outDir)
	err := CreateProject(outDir, blockName, false)
	if err != nil {
		t.Errorf("Test failed: %s", err.Error())
	}
}

func TestBootstrapWithReadmeTemplate(t *testing.T) {
	outDir := "sample_project_template"
	blockName := "AwesomeBlock"
	defer deleteDir(outDir)
	err := CreateProject(outDir, blockName, true)
	if err != nil {
		t.Errorf("Test failed: %s", err.Error())
	}

	readmePath := filepath.Join(outDir, "awesome_block", "docs", "README.md")
	content, err := os.ReadFile(readmePath)
	if err != nil {
		t.Fatalf("Failed to read README.md: %s", err.Error())
	}
	if !strings.Contains(string(content), "addUrl") {
		t.Errorf("Expected README.md to contain addUrl template syntax")
	}
}