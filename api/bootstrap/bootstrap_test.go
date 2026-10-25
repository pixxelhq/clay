package bootstrap

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func TestCreateProject_GeneratesExpectedLayout(t *testing.T) {
	outDir := t.TempDir()
	blockName := "AwesomeBlock"

	if err := CreateProject(outDir, blockName, false); err != nil {
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
	err := CreateProject(outDir, "bad_block_name_123", false)
	if err == nil {
		t.Fatal("expected error for non-alpha block name, got nil")
	}
}

// writeLeftover creates <outDir>/awesome_block/leftover.txt and returns its path.
func writeLeftover(t *testing.T, outDir string) string {
	t.Helper()
	existing := filepath.Join(outDir, "awesome_block", "leftover.txt")
	if err := os.MkdirAll(filepath.Dir(existing), 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(existing, []byte("keep me"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}
	return existing
}

func TestCreateProject_RejectsNonEmptyProjectDir(t *testing.T) {
	outDir := t.TempDir()
	existing := writeLeftover(t, outDir)

	err := CreateProject(outDir, "AwesomeBlock", false)
	if !errors.Is(err, ErrProjectDirNotEmpty) {
		t.Fatalf("expected ErrProjectDirNotEmpty, got: %v", err)
	}

	entries, err := os.ReadDir(filepath.Dir(existing))
	if err != nil {
		t.Fatalf("reading project dir: %v", err)
	}
	if len(entries) != 1 || entries[0].Name() != "leftover.txt" {
		t.Errorf("expected project dir to be unchanged, got %d entries", len(entries))
	}
	if data, err := os.ReadFile(existing); err != nil || string(data) != "keep me" {
		t.Errorf("expected leftover file to be unchanged, got %q (err: %v)", data, err)
	}
}

func TestCreateProject_ForceKeepsNonTemplateFiles(t *testing.T) {
	outDir := t.TempDir()
	existing := writeLeftover(t, outDir)

	if err := CreateProject(outDir, "AwesomeBlock", true); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}

	if data, err := os.ReadFile(existing); err != nil || string(data) != "keep me" {
		t.Errorf("expected leftover file to be kept, got %q (err: %v)", data, err)
	}
	if _, err := os.Stat(filepath.Join(outDir, "awesome_block", "clay.yaml")); err != nil {
		t.Errorf("expected generated clay.yaml: %v", err)
	}
}

func TestCreateProject_EmptyExistingProjectDir(t *testing.T) {
	outDir := t.TempDir()
	if err := os.Mkdir(filepath.Join(outDir, "awesome_block"), 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}

	if err := CreateProject(outDir, "AwesomeBlock", false); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}

	if _, err := os.Stat(filepath.Join(outDir, "awesome_block", "clay.yaml")); err != nil {
		t.Errorf("expected generated clay.yaml: %v", err)
	}
}

func TestCreateProject_OutputDirContainingSrc(t *testing.T) {
	outDir := filepath.Join(t.TempDir(), "srcbug", "src", "work")
	if err := os.MkdirAll(outDir, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}

	if err := CreateProject(outDir, "AwesomeBlock", false); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}

	projectRoot := filepath.Join(outDir, "awesome_block")
	for _, rel := range []string{"clay.yaml", filepath.Join("awesome_block", "block.py")} {
		if _, err := os.Stat(filepath.Join(projectRoot, rel)); err != nil {
			t.Errorf("expected %q under the requested output dir: %v", rel, err)
		}
	}
}
