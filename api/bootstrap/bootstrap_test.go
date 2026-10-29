package bootstrap

import (
	"errors"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
)

// listFiles returns the slash-separated paths of the files under root.
func listFiles(t *testing.T, root string) []string {
	t.Helper()
	var files []string
	err := filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		rel, err := filepath.Rel(root, path)
		files = append(files, filepath.ToSlash(rel))
		return err
	})
	if err != nil {
		t.Fatalf("walking %s: %v", root, err)
	}
	slices.Sort(files)
	return files
}

// defaultFiles is the project that clay new creates without --with.
var defaultFiles = []string{
	".dockerignore",
	".gitignore",
	"README.md",
	"awesome_block/block.py",
	"awesome_block/entry.py",
	"clay.yaml",
	"pyproject.toml",
	"requirements-dev.txt",
	"requirements.txt",
	"tests/sample_block_inputs.json",
	"tests/test_block.py",
}

func TestCreateProject_GeneratesMinimalProject(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "awesome-block")
	if err := CreateProject(projectRoot, "awesome-block", false, nil); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}
	if got := listFiles(t, projectRoot); !slices.Equal(got, defaultFiles) {
		t.Errorf("generated files:\n got  %v\n want %v", got, defaultFiles)
	}
}

func TestCreateProject_WithOptionsAddsFiles(t *testing.T) {
	tests := []struct {
		with  []string
		added []string
	}{
		{[]string{"catalog"}, []string{"catalog.yaml"}},
		{[]string{"conda"}, []string{"conda.yaml"}},
		{[]string{"pre-commit"}, []string{".pre-commit-config.yaml"}},
		{Options, []string{"catalog.yaml", "conda.yaml", ".pre-commit-config.yaml"}},
	}
	for _, tt := range tests {
		t.Run(strings.Join(tt.with, ","), func(t *testing.T) {
			projectRoot := filepath.Join(t.TempDir(), "awesome-block")
			if err := CreateProject(projectRoot, "awesome-block", false, tt.with); err != nil {
				t.Fatalf("CreateProject returned error: %v", err)
			}
			want := slices.Concat(defaultFiles, tt.added)
			slices.Sort(want)
			if got := listFiles(t, projectRoot); !slices.Equal(got, want) {
				t.Errorf("generated files:\n got  %v\n want %v", got, want)
			}
		})
	}
}

func TestCreateProject_WithCondaBuildsWithConda(t *testing.T) {
	read := func(with []string, rel string) string {
		t.Helper()
		projectRoot := filepath.Join(t.TempDir(), "awesome-block")
		if err := CreateProject(projectRoot, "awesome-block", false, with); err != nil {
			t.Fatalf("CreateProject returned error: %v", err)
		}
		data, err := os.ReadFile(filepath.Join(projectRoot, rel))
		if err != nil {
			t.Fatalf("reading %s: %v", rel, err)
		}
		return string(data)
	}

	conda := read([]string{"conda"}, "clay.yaml")
	for _, want := range []string{"  conda: true\n", "  requirements: conda.yaml\n"} {
		if !strings.Contains(conda, want) {
			t.Errorf("clay.yaml with conda does not contain %q:\n%s", want, conda)
		}
	}
	pip := read(nil, "clay.yaml")
	for _, want := range []string{"  conda: false\n", "  requirements: requirements.txt\n"} {
		if !strings.Contains(pip, want) {
			t.Errorf("default clay.yaml does not contain %q:\n%s", want, pip)
		}
	}
}

func TestCreateProject_WithPreCommit(t *testing.T) {
	for _, tt := range []struct {
		with []string
		want bool
	}{{nil, false}, {[]string{"pre-commit"}, true}} {
		projectRoot := filepath.Join(t.TempDir(), "awesome-block")
		if err := CreateProject(projectRoot, "awesome-block", false, tt.with); err != nil {
			t.Fatalf("CreateProject returned error: %v", err)
		}
		for _, rel := range []string{"requirements-dev.txt", "README.md"} {
			data, err := os.ReadFile(filepath.Join(projectRoot, rel))
			if err != nil {
				t.Fatalf("reading %s: %v", rel, err)
			}
			if got := strings.Contains(string(data), "pre-commit"); got != tt.want {
				t.Errorf("with %v: %s mentions pre-commit = %v, want %v:\n%s", tt.with, rel, got, tt.want, data)
			}
		}
	}
}

// The optional pre-commit config must not impose a commit message policy.
func TestCreateProject_PreCommitHasNoCommitMessageHook(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "awesome-block")
	if err := CreateProject(projectRoot, "awesome-block", false, []string{"pre-commit"}); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}
	data, err := os.ReadFile(filepath.Join(projectRoot, ".pre-commit-config.yaml"))
	if err != nil {
		t.Fatalf("reading .pre-commit-config.yaml: %v", err)
	}
	if strings.Contains(string(data), "commit-msg") {
		t.Errorf(".pre-commit-config.yaml has a commit-msg hook:\n%s", data)
	}
}

func TestCreateProject_RejectsUnknownOption(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "awesome-block")
	err := CreateProject(projectRoot, "awesome-block", false, []string{"catalog", "makefile"})
	if err == nil || !strings.Contains(err.Error(), `"makefile"`) || !strings.Contains(err.Error(), "pre-commit") {
		t.Fatalf("expected an unknown option error listing the valid options, got: %v", err)
	}
	if _, err := os.Stat(projectRoot); !os.IsNotExist(err) {
		t.Errorf("expected no project dir, stat err: %v", err)
	}
}

// Development tools must not be in requirements.txt, which goes into the image.
func TestCreateProject_SplitsRuntimeAndDevRequirements(t *testing.T) {
	old := ClayVersion
	ClayVersion = "9.8.7"
	t.Cleanup(func() { ClayVersion = old })

	projectRoot := filepath.Join(t.TempDir(), "awesome-block")
	if err := CreateProject(projectRoot, "awesome-block", false, nil); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}
	read := func(rel string) string {
		t.Helper()
		data, err := os.ReadFile(filepath.Join(projectRoot, rel))
		if err != nil {
			t.Fatalf("reading %s: %v", rel, err)
		}
		return string(data)
	}

	runtime := read("requirements.txt")
	if !strings.Contains(runtime, "pixxel-clay==9.8.7\n") {
		t.Errorf("requirements.txt does not pin pixxel-clay==9.8.7:\n%s", runtime)
	}
	for _, tool := range []string{"ruff", "pyright", "pytest", "pre-commit"} {
		if strings.Contains(runtime, tool) {
			t.Errorf("requirements.txt contains dev tool %q:\n%s", tool, runtime)
		}
	}

	dev := read("requirements-dev.txt")
	if !strings.HasPrefix(dev, "-r requirements.txt\n") {
		t.Errorf("requirements-dev.txt does not start with -r requirements.txt:\n%s", dev)
	}
	for _, tool := range []string{"ruff", "pyright", "pytest"} {
		if !strings.Contains(dev, tool+"\n") {
			t.Errorf("requirements-dev.txt is missing %q:\n%s", tool, dev)
		}
	}

	ignored := strings.Split(read(".dockerignore"), "\n")
	for _, want := range []string{".venv", "**/__pycache__", "tests", ".git"} {
		if !slices.Contains(ignored, want) {
			t.Errorf(".dockerignore is missing %q", want)
		}
	}
}

func TestCreateProject_RejectsInvalidBlockName(t *testing.T) {
	outDir := t.TempDir()
	err := CreateProject(filepath.Join(outDir, "awesome-block"), "1bad block", false, nil)
	if err == nil {
		t.Fatal("expected error for invalid block name, got nil")
	}
}

// "awesome-block" and "awesome_block" must render the same files.
func TestCreateProject_UsesCanonicalNames(t *testing.T) {
	want := map[string]string{
		"clay.yaml": "name: awesome-block\n",
		"README.md": "# AwesomeBlock",
		filepath.Join("awesome_block", "block.py"): "class AwesomeBlock(BlockWrapper)",
		filepath.Join("awesome_block", "entry.py"): "from block import AwesomeBlock",
		filepath.Join("tests", "test_block.py"):    "from awesome_block.block import AwesomeBlock",
	}
	for _, input := range []string{"awesome-block", "awesome_block", "AwesomeBlock"} {
		t.Run(input, func(t *testing.T) {
			outDir := t.TempDir()
			if err := CreateProject(filepath.Join(outDir, "awesome-block"), input, false, nil); err != nil {
				t.Fatalf("CreateProject returned error: %v", err)
			}
			for rel, snippet := range want {
				data, err := os.ReadFile(filepath.Join(outDir, "awesome-block", rel))
				if err != nil {
					t.Fatalf("reading %s: %v", rel, err)
				}
				if !strings.Contains(string(data), snippet) {
					t.Errorf("%s does not contain %q", rel, snippet)
				}
			}
		})
	}
}

// writeLeftover creates <outDir>/awesome-block/leftover.txt and returns its path.
func writeLeftover(t *testing.T, outDir string) string {
	t.Helper()
	existing := filepath.Join(outDir, "awesome-block", "leftover.txt")
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

	err := CreateProject(filepath.Join(outDir, "awesome-block"), "awesome-block", false, nil)
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

	if err := CreateProject(filepath.Join(outDir, "awesome-block"), "awesome-block", true, nil); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}

	if data, err := os.ReadFile(existing); err != nil || string(data) != "keep me" {
		t.Errorf("expected leftover file to be kept, got %q (err: %v)", data, err)
	}
	if _, err := os.Stat(filepath.Join(outDir, "awesome-block", "clay.yaml")); err != nil {
		t.Errorf("expected generated clay.yaml: %v", err)
	}
}

func TestCreateProject_EmptyExistingProjectDir(t *testing.T) {
	outDir := t.TempDir()
	if err := os.Mkdir(filepath.Join(outDir, "awesome-block"), 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}

	if err := CreateProject(filepath.Join(outDir, "awesome-block"), "awesome-block", false, nil); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}

	if _, err := os.Stat(filepath.Join(outDir, "awesome-block", "clay.yaml")); err != nil {
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

	if err := CreateProject(filepath.Join(outDir, "awesome-block"), "awesome-block", false, nil); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}

	projectRoot := filepath.Join(outDir, "awesome-block")
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
	projectRoot := filepath.Join(outDir, "awesome-block")
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	clayYAML := filepath.Join(projectRoot, "clay.yaml")
	if err := os.WriteFile(clayYAML, []byte("mine"), 0444); err != nil {
		t.Fatalf("setup: %v", err)
	}

	err := CreateProject(filepath.Join(outDir, "awesome-block"), "awesome-block", true, nil)
	if !errors.Is(err, fs.ErrPermission) {
		t.Fatalf("expected a permission error, got: %v", err)
	}
}

func TestCreateProject_ReturnsMkdirError(t *testing.T) {
	outDir := t.TempDir()
	projectRoot := filepath.Join(outDir, "awesome-block")
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	// "tests" is a file, so the template's tests/ folder cannot be created
	if err := os.WriteFile(filepath.Join(projectRoot, "tests"), []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}

	var err error
	out := captureStdout(t, func() { err = CreateProject(filepath.Join(outDir, "awesome-block"), "awesome-block", true, nil) })
	if err == nil {
		t.Fatal("expected an error, got nil")
	}
	if strings.Contains(out, "Created: "+filepath.Join(projectRoot, "tests")+"\n") {
		t.Errorf("printed Created: for a folder that was not created:\n%s", out)
	}
}

func TestCreateProject_ReportsOverwrittenFiles(t *testing.T) {
	outDir := t.TempDir()
	projectRoot := filepath.Join(outDir, "awesome-block")
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(filepath.Join(projectRoot, "clay.yaml"), []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}

	var err error
	out := captureStdout(t, func() { err = CreateProject(filepath.Join(outDir, "awesome-block"), "awesome-block", true, nil) })
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
	if err := CreateProject(filepath.Join(outDir, "awesome-block"), "awesome-block", false, Options); err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}
	err := filepath.WalkDir(filepath.Join(outDir, "awesome-block"), func(path string, d fs.DirEntry, err error) error {
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

// Scaffolding the current directory must not tell the user to cd into it.
func TestCreateProject_NextStepsSkipCdForCurrentDir(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "awesome-block")
	if err := os.Mkdir(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	old, err := os.Getwd()
	if err != nil {
		t.Fatalf("getwd: %v", err)
	}
	if err := os.Chdir(projectRoot); err != nil {
		t.Fatalf("chdir: %v", err)
	}
	t.Cleanup(func() { _ = os.Chdir(old) })

	out := captureStdout(t, func() { err = CreateProject(".", "awesome-block", false, nil) })
	if err != nil {
		t.Fatalf("CreateProject returned error: %v", err)
	}
	if strings.Contains(out, "  cd ") {
		t.Errorf("next steps tell the user to cd into the current directory:\n%s", out)
	}
}
