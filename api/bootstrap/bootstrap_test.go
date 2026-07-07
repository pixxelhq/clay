package bootstrap

import (
	"os"
	"path/filepath"
	"testing"
)

func TestCreateProject_GeneratesExpectedLayout(t *testing.T) {
	outDir := t.TempDir()
	blockName := "AwesomeBlock"

	if err := CreateProject(outDir, blockName); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}

	projectRoot := filepath.Join(outDir, "awesome_block")

	expectedFiles := []string{
		"Makefile",
		"README.md",
		"clay.yaml",
		"catalog.yaml",
		"conda.yaml",
		"pyproject.toml",
		"requirements.txt",
		filepath.Join("awesome_block", "block.py"),
		filepath.Join("awesome_block", "entry.py"),
		filepath.Join("tests", "test_block.py"),
		filepath.Join("tests", "sample_block_inputs.json"),
	}
	for _, rel := range expectedFiles {
		path := filepath.Join(projectRoot, rel)
		if _, err := os.Stat(path); err != nil {
			t.Errorf("expected generated file %q missing: %v", rel, err)
		}
	}

	expectedDirs := []string{"tests", "awesome_block"}
	for _, rel := range expectedDirs {
		info, err := os.Stat(filepath.Join(projectRoot, rel))
		if err != nil {
			t.Errorf("expected directory %q missing: %v", rel, err)
			continue
		}
		if !info.IsDir() {
			t.Errorf("%q should be a directory", rel)
		}
	}
}

func TestCreateProject_RejectsNonAlphaBlockName(t *testing.T) {
	outDir := t.TempDir()
	err := CreateProject(outDir, "bad_block_name_123")
	if err == nil {
		t.Fatal("expected error for non-alpha block name, got nil")
	}
}

func TestCreateProject_OverwritesExistingProjectDir(t *testing.T) {
	outDir := t.TempDir()
	existing := filepath.Join(outDir, "awesome_block", "leftover.txt")
	if err := os.MkdirAll(filepath.Dir(existing), 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(existing, []byte("stale"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}

	if err := CreateProject(outDir, "AwesomeBlock"); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}

	if _, err := os.Stat(existing); !os.IsNotExist(err) {
		t.Errorf("expected leftover file to be cleaned up, stat err: %v", err)
	}
}
