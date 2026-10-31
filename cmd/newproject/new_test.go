package newproject

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
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

	if err := runNew([]string{outDir, "WeatherForecaster"}); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}

	projectRoot := filepath.Join(outDir, "weather_forecaster")
	if _, err := os.Stat(filepath.Join(projectRoot, "clay.yaml")); err != nil {
		t.Errorf("expected generated clay.yaml: %v", err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "weather_forecaster", "block.py")); err != nil {
		t.Errorf("expected generated block.py: %v", err)
	}
}

func TestNewCmd_RunEPropagatesInvalidName(t *testing.T) {
	outDir := t.TempDir()

	err := runNew([]string{outDir, "bad_name_123"})
	if err == nil {
		t.Fatal("expected error for non-alpha block name, got nil")
	}
}

func TestNewCmd_RunERejectsNonEmptyDirWithHint(t *testing.T) {
	outDir := t.TempDir()
	projectRoot := filepath.Join(outDir, "weather_forecaster")
	if err := os.MkdirAll(projectRoot, 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(filepath.Join(projectRoot, "notes.txt"), []byte("mine"), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}

	err := runNew([]string{outDir, "WeatherForecaster"})
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
	projectRoot := filepath.Join(outDir, "weather_forecaster")
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

	if err := cmd.RunE(cmd, []string{outDir, "WeatherForecaster"}); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}
	if _, err := os.Stat(notes); err != nil {
		t.Errorf("expected notes.txt to be kept: %v", err)
	}
	if _, err := os.Stat(filepath.Join(projectRoot, "clay.yaml")); err != nil {
		t.Errorf("expected generated clay.yaml: %v", err)
	}
}

// runNew runs a new `clay new` command with args.
func runNew(args []string) error {
	cmd := NewCmd()
	return cmd.RunE(cmd, args)
}
