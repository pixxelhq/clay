package newproject

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/pixxelhq/clay/api/bootstrap"
)

func TestNewCmd_Metadata(t *testing.T) {
	cmd := NewCmd()
	if cmd.Use == "" {
		t.Error("NewCmd().Use should not be empty")
	}
	if cmd.Short == "" {
		t.Error("NewCmd().Short should not be empty")
	}
	if cmd.RunE == nil {
		t.Fatal("NewCmd().RunE should not be nil")
	}
}

func TestNewCmd_RunEScaffoldsProject(t *testing.T) {
	outDir := t.TempDir()

	projectRoot := filepath.Join(outDir, "weather-forecaster")
	if err := runNew([]string{projectRoot}); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}

	if _, err := os.Stat(filepath.Join(projectRoot, "clay.yaml")); err != nil {
		t.Errorf("expected generated clay.yaml: %v", err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "weather_forecaster", "block.py")); err != nil {
		t.Errorf("expected generated block.py: %v", err)
	}
}

func TestNewCmd_RunEPropagatesInvalidName(t *testing.T) {
	outDir := t.TempDir()

	err := runNew([]string{filepath.Join(outDir, "bad name")})
	if err == nil {
		t.Fatal("expected error for invalid block name, got nil")
	}
}

func TestNewCmd_RunERejectsNonEmptyDirWithHint(t *testing.T) {
	outDir := t.TempDir()
	projectRoot := filepath.Join(outDir, "weather-forecaster")
	notes := filepath.Join(projectRoot, "notes.txt")
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(notes, []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}

	err := runNew([]string{projectRoot})
	if !errors.Is(err, errDirNotEmpty) || !strings.Contains(err.Error(), "clay init") {
		t.Errorf("expected errDirNotEmpty with a clay init hint, got: %v", err)
	}
	entries, err := os.ReadDir(projectRoot)
	if err != nil {
		t.Fatalf("reading project dir: %v", err)
	}
	if len(entries) != 1 {
		t.Errorf("expected project dir to be unchanged, got %d entries", len(entries))
	}
}

func TestNewCmd_EmptyExistingDir(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "weather-forecaster")
	if err := os.Mkdir(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}

	if err := runNew([]string{projectRoot}); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "clay.yaml")); err != nil {
		t.Errorf("expected generated clay.yaml: %v", err)
	}
}

func TestNewCmd_HasNoForceFlag(t *testing.T) {
	if NewCmd().Flags().Lookup("force") != nil {
		t.Error("clay new must not have --force; clay init handles existing directories")
	}
}

func TestNewCmd_DeprecatedTwoArgForm(t *testing.T) {
	outDir := t.TempDir()
	var stderr bytes.Buffer
	cmd := NewCmd()
	cmd.SetErr(&stderr)

	if err := cmd.RunE(cmd, []string{outDir, "WeatherForecaster"}); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	if _, err := os.Stat(filepath.Join(outDir, "weather-forecaster", "clay.yaml")); err != nil {
		t.Errorf("expected project in <path>/<slug>: %v", err)
	}
	if !strings.Contains(stderr.String(), "deprecated") {
		t.Errorf("expected a deprecation warning, got %q", stderr.String())
	}
}

func TestNewCmd_CurrentDir(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "weather-forecaster")
	if err := os.Mkdir(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	chdir(t, projectRoot)

	if err := runNew([]string{"."}); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	data, err := os.ReadFile(filepath.Join(projectRoot, "clay.yaml"))
	if err != nil || !strings.Contains(string(data), "name: weather-forecaster") {
		t.Errorf("expected clay.yaml named after the directory, got %q (err: %v)", data, err)
	}
}

func TestInitCmd_ScaffoldsCurrentDir(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "weather_forecaster")
	if err := os.Mkdir(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	chdir(t, projectRoot)

	if err := runInit(); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	data, err := os.ReadFile(filepath.Join(projectRoot, "clay.yaml"))
	if err != nil || !strings.Contains(string(data), "name: weather-forecaster") {
		t.Errorf("expected clay.yaml named after the directory, got %q (err: %v)", data, err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "weather_forecaster", "block.py")); err != nil {
		t.Errorf("expected generated block.py: %v", err)
	}
}

func TestInitCmd_ScaffoldsNonEmptyDir(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "weather-forecaster")
	readme := filepath.Join(projectRoot, "README.md")
	if err := os.Mkdir(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(readme, []byte("my readme"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}
	chdir(t, projectRoot)

	if err := runInit(); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	if data, err := os.ReadFile(readme); err != nil || string(data) != "my readme" {
		t.Errorf("expected README.md to be kept, got %q (err: %v)", data, err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "clay.yaml")); err != nil {
		t.Errorf("expected generated clay.yaml: %v", err)
	}
}

func TestInitCmd_ForceFlagOverwritesExistingProject(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "weather-forecaster")
	notes := filepath.Join(projectRoot, "notes.txt")
	clayYAML := filepath.Join(projectRoot, "clay.yaml")
	if err := os.Mkdir(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(notes, []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(clayYAML, []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}
	chdir(t, projectRoot)

	cmd := InitCmd()
	if err := cmd.Flags().Set("force", "true"); err != nil {
		t.Fatalf("setting --force: %v", err)
	}
	if err := cmd.RunE(cmd, nil); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	if _, err := os.Stat(notes); err != nil {
		t.Errorf("expected notes.txt to be kept: %v", err)
	}
	if data, err := os.ReadFile(clayYAML); err != nil || !strings.Contains(string(data), "name: weather-forecaster") {
		t.Errorf("expected clay.yaml to be overwritten, got %q (err: %v)", data, err)
	}
}

func TestInitCmd_RejectsExistingProject(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "weather-forecaster")
	if err := os.Mkdir(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(filepath.Join(projectRoot, "clay.yaml"), []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}
	chdir(t, projectRoot)

	err := runInit()
	if !errors.Is(err, bootstrap.ErrProjectExists) || !strings.Contains(err.Error(), "--force") {
		t.Fatalf("expected ErrProjectExists with --force hint, got: %v", err)
	}
}

func TestNewCmd_NameFlag(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "resnet.v2")
	cmd := NewCmd()
	if err := cmd.Flags().Set("name", "HTTPServer"); err != nil {
		t.Fatalf("setting --name: %v", err)
	}

	if err := cmd.RunE(cmd, []string{projectRoot}); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	data, err := os.ReadFile(filepath.Join(projectRoot, "clay.yaml"))
	if err != nil || !strings.Contains(string(data), "name: httpserver") {
		t.Errorf("expected clay.yaml named after --name, got %q (err: %v)", data, err)
	}
}

func TestNewCmd_InvalidDirNameSuggestsNameFlag(t *testing.T) {
	err := runNew([]string{filepath.Join(t.TempDir(), "resnet.v2")})
	if err == nil || !strings.Contains(err.Error(), `directory name "resnet.v2"`) || !strings.Contains(err.Error(), "--name") {
		t.Errorf("expected error naming the directory and --name, got: %v", err)
	}
}

func TestNewCmd_DeprecatedFormWarningKeepsName(t *testing.T) {
	outDir := t.TempDir()
	var stderr bytes.Buffer
	cmd := NewCmd()
	cmd.SetErr(&stderr)

	if err := cmd.RunE(cmd, []string{outDir, "HTTPServer"}); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	want := "use 'clay new " + filepath.Join(outDir, "httpserver") + " --name HTTPServer'"
	if !strings.Contains(stderr.String(), want) {
		t.Errorf("expected warning to contain %q, got %q", want, stderr.String())
	}
}

func TestNewCmd_DeprecatedFormRejectsNameFlag(t *testing.T) {
	cmd := NewCmd()
	if err := cmd.Flags().Set("name", "other"); err != nil {
		t.Fatalf("setting --name: %v", err)
	}
	if err := cmd.RunE(cmd, []string{t.TempDir(), "my-block"}); err == nil {
		t.Fatal("expected error for --name with the deprecated form, got nil")
	}
}

func TestInitCmd_NameFlag(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "resnet.v2")
	if err := os.Mkdir(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	chdir(t, projectRoot)
	cmd := InitCmd()
	if err := cmd.Flags().Set("name", "resnet-v2"); err != nil {
		t.Fatalf("setting --name: %v", err)
	}

	if err := cmd.RunE(cmd, nil); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "resnet_v2", "block.py")); err != nil {
		t.Errorf("expected generated block.py: %v", err)
	}
}

func TestInitCmd_RefusesHomeAndStandardFolders(t *testing.T) {
	home := t.TempDir()
	setHomeDir(t, home)

	for _, dir := range []string{home, filepath.Join(home, "Desktop"), filepath.Join(home, "Documents"), filepath.Join(home, "Downloads")} {
		t.Run(filepath.Base(dir), func(t *testing.T) {
			if err := os.MkdirAll(dir, 0755); err != nil {
				t.Fatalf("setup: %v", err)
			}
			chdir(t, dir)
			cmd := InitCmd()
			if err := cmd.Flags().Set("force", "true"); err != nil {
				t.Fatalf("setting --force: %v", err)
			}

			err := cmd.RunE(cmd, nil)
			if err == nil || !strings.Contains(err.Error(), "clay init does not use") || !strings.Contains(err.Error(), "clay new") {
				t.Errorf("expected a refusal with a clay new hint, got: %v", err)
			}
			if _, err := os.Stat(filepath.Join(dir, "clay.yaml")); !os.IsNotExist(err) {
				t.Errorf("expected no template files to be written, stat err: %v", err)
			}
		})
	}
}

func TestInitCmd_AllowsFolderInsideStandardFolder(t *testing.T) {
	home := t.TempDir()
	setHomeDir(t, home)
	projectRoot := filepath.Join(home, "Documents", "my-model")
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	chdir(t, projectRoot)

	if err := runInit(); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "clay.yaml")); err != nil {
		t.Errorf("expected generated clay.yaml: %v", err)
	}
}

func TestEnsureNotPersonalFolder_RefusesFilesystemRoot(t *testing.T) {
	root, err := filepath.Abs(string(filepath.Separator))
	if err != nil {
		t.Fatalf("abs: %v", err)
	}
	if err := ensureNotPersonalFolder(root); err == nil || !strings.Contains(err.Error(), "filesystem root") {
		t.Errorf("expected a refusal for %s, got: %v", root, err)
	}
}

func setHomeDir(t *testing.T, home string) {
	t.Helper()
	t.Setenv("HOME", home)
	t.Setenv("USERPROFILE", home)
}

// chdir changes the working directory for the rest of the test.
func chdir(t *testing.T, dir string) {
	t.Helper()
	old, err := os.Getwd()
	if err != nil {
		t.Fatalf("getwd: %v", err)
	}
	if err := os.Chdir(dir); err != nil {
		t.Fatalf("chdir: %v", err)
	}
	t.Cleanup(func() { _ = os.Chdir(old) })
}

// runNew runs a new `clay new` command with args.
func runNew(args []string) error {
	cmd := NewCmd()
	return cmd.RunE(cmd, args)
}

// runInit runs a new `clay init` command.
func runInit() error {
	cmd := InitCmd()
	return cmd.RunE(cmd, nil)
}
