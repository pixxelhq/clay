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
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(filepath.Join(projectRoot, "notes.txt"), []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}

	err := runNew([]string{projectRoot})
	if err == nil {
		t.Fatal("expected error for non-empty project dir, got nil")
	}
	if !strings.Contains(err.Error(), "already exists and is not empty") || !strings.Contains(err.Error(), "--force") {
		t.Errorf("expected not-empty error with --force hint, got: %v", err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "clay.yaml")); !os.IsNotExist(err) {
		t.Errorf("expected no template files to be written, stat err: %v", err)
	}
}

func TestNewCmd_ForceFlagWritesIntoNonEmptyDir(t *testing.T) {
	outDir := t.TempDir()
	projectRoot := filepath.Join(outDir, "weather-forecaster")
	notes := filepath.Join(projectRoot, "notes.txt")
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(notes, []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}

	cmd := NewCmd()
	if err := cmd.Flags().Set("force", "true"); err != nil {
		t.Fatalf("setting --force: %v", err)
	}

	if err := cmd.RunE(cmd, []string{projectRoot}); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	if _, err := os.Stat(notes); err != nil {
		t.Errorf("expected notes.txt to be kept: %v", err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "clay.yaml")); err != nil {
		t.Errorf("expected generated clay.yaml: %v", err)
	}
}

func TestNewCmd_WithFlag(t *testing.T) {
	for _, values := range [][]string{{"catalog,pre-commit"}, {"catalog", "pre-commit"}} {
		projectRoot := filepath.Join(t.TempDir(), "weather-forecaster")
		cmd := NewCmd()
		for _, v := range values {
			if err := cmd.Flags().Set("with", v); err != nil {
				t.Fatalf("setting --with %s: %v", v, err)
			}
		}
		if err := cmd.RunE(cmd, []string{projectRoot}); err != nil {
			t.Fatalf("--with %v: RunE returned error: %v", values, err)
		}
		for _, rel := range []string{"catalog.yaml", ".pre-commit-config.yaml"} {
			if _, err := os.Stat(filepath.Join(projectRoot, rel)); err != nil {
				t.Errorf("--with %v: expected %s: %v", values, rel, err)
			}
		}
		if _, err := os.Stat(filepath.Join(projectRoot, "conda.yaml")); !os.IsNotExist(err) {
			t.Errorf("--with %v: expected no conda.yaml, stat err: %v", values, err)
		}
	}
}

func TestNewCmd_WithFlagRejectsUnknownOption(t *testing.T) {
	cmd := NewCmd()
	if err := cmd.Flags().Set("with", "makefile"); err != nil {
		t.Fatalf("setting --with: %v", err)
	}
	err := cmd.RunE(cmd, []string{filepath.Join(t.TempDir(), "weather-forecaster")})
	if err == nil || !strings.Contains(err.Error(), "makefile") {
		t.Fatalf("expected an unknown option error, got: %v", err)
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

func TestInitCmd_WithFlag(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "weather_forecaster")
	if err := os.Mkdir(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	chdir(t, projectRoot)

	cmd := InitCmd()
	if err := cmd.Flags().Set("with", "conda"); err != nil {
		t.Fatalf("setting --with: %v", err)
	}
	if err := cmd.RunE(cmd, nil); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "conda.yaml")); err != nil {
		t.Errorf("expected conda.yaml: %v", err)
	}
}

func TestInitCmd_RejectsNonEmptyDir(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "weather-forecaster")
	if err := os.Mkdir(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(filepath.Join(projectRoot, "notes.txt"), []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}
	chdir(t, projectRoot)

	err := runInit()
	if !errors.Is(err, bootstrap.ErrProjectDirNotEmpty) {
		t.Fatalf("expected ErrProjectDirNotEmpty, got: %v", err)
	}
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
