package bootstrap

import (
	"errors"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
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

func TestCreateProject_OutputDirContainingSrcTwice(t *testing.T) {
	// "src" appears twice in the output path; only the template's own src/
	// may be renamed, and nothing may be created outside the project dir.
	base := t.TempDir()
	outDir := filepath.Join(base, "src", "projects", "src", "work")
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
	if _, err := os.Stat(filepath.Join(projectRoot, "src")); !os.IsNotExist(err) {
		t.Errorf("expected template src/ to be renamed, stat err: %v", err)
	}

	// everything under base must be the project itself or one of the
	// directories created during setup
	setupDirs := map[string]bool{base: true}
	for dir := outDir; dir != base; dir = filepath.Dir(dir) {
		setupDirs[dir] = true
	}
	err := filepath.WalkDir(base, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if path == projectRoot {
			return filepath.SkipDir
		}
		if !setupDirs[path] {
			t.Errorf("unexpected path created outside the project dir: %s", path)
		}
		return nil
	})
	if err != nil {
		t.Fatalf("walking %s: %v", base, err)
	}
}

// captureStdout returns what fn prints to stdout.
func captureStdout(t *testing.T, fn func()) string {
	t.Helper()
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("pipe: %v", err)
	}
	old := os.Stdout
	os.Stdout = w
	defer func() { os.Stdout = old }()
	fn()
	w.Close()
	out, err := io.ReadAll(r)
	if err != nil {
		t.Fatalf("reading stdout: %v", err)
	}
	return string(out)
}

func TestCreateProject_ReturnsTemplateWriteError(t *testing.T) {
	if os.Geteuid() == 0 {
		t.Skip("root can write read-only files")
	}
	outDir := t.TempDir()
	projectRoot := filepath.Join(outDir, "awesome_block")
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	clayYAML := filepath.Join(projectRoot, "clay.yaml")
	if err := os.WriteFile(clayYAML, []byte("mine"), 0444); err != nil {
		t.Fatalf("setup: %v", err)
	}

	err := CreateProject(outDir, "AwesomeBlock", true)
	if !errors.Is(err, fs.ErrPermission) {
		t.Fatalf("expected a permission error, got: %v", err)
	}
}

func TestCreateProject_ReturnsMkdirError(t *testing.T) {
	outDir := t.TempDir()
	projectRoot := filepath.Join(outDir, "awesome_block")
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	// "tests" is a file, so the template's tests/ folder cannot be created
	if err := os.WriteFile(filepath.Join(projectRoot, "tests"), []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}

	var err error
	out := captureStdout(t, func() { err = CreateProject(outDir, "AwesomeBlock", true) })
	if err == nil {
		t.Fatal("expected an error, got nil")
	}
	if strings.Contains(out, "Created: "+filepath.Join(projectRoot, "tests")+"\n") {
		t.Errorf("printed Created: for a folder that was not created:\n%s", out)
	}
}

func TestCreateProject_ReportsOverwrittenFiles(t *testing.T) {
	outDir := t.TempDir()
	projectRoot := filepath.Join(outDir, "awesome_block")
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(filepath.Join(projectRoot, "clay.yaml"), []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}

	var err error
	out := captureStdout(t, func() { err = CreateProject(outDir, "AwesomeBlock", true) })
	if err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}
	if !strings.Contains(out, "Overwrote: "+filepath.Join(projectRoot, "clay.yaml")+"\n") {
		t.Errorf("expected Overwrote: for clay.yaml, got:\n%s", out)
	}
	if !strings.Contains(out, "Created: "+filepath.Join(projectRoot, "README.md")+"\n") {
		t.Errorf("expected Created: for README.md, got:\n%s", out)
	}
}

// Template files must be rendered on every OS; on Windows, OS-style template
// paths once made the lookups miss and left the placeholders in the files.
func TestCreateProject_RendersAllTemplates(t *testing.T) {
	outDir := t.TempDir()
	if err := CreateProject(outDir, "AwesomeBlock", false); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}
	err := filepath.WalkDir(filepath.Join(outDir, "awesome_block"), func(path string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		if strings.Contains(string(data), "{{") {
			t.Errorf("%s still has template placeholders", path)
		}
		return nil
	})
	if err != nil {
		t.Fatalf("walking project: %v", err)
	}
}
