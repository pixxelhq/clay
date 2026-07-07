package newproject

import (
	"os"
	"path/filepath"
	"testing"
)

func TestNewCmd_Metadata(t *testing.T) {
	if NewCmd.Use == "" {
		t.Error("NewCmd.Use should not be empty")
	}
	if NewCmd.Short == "" {
		t.Error("NewCmd.Short should not be empty")
	}
	if NewCmd.RunE == nil {
		t.Fatal("NewCmd.RunE should not be nil")
	}
}

func TestNewCmd_RunEScaffoldsProject(t *testing.T) {
	outDir := t.TempDir()

	if err := NewCmd.RunE(NewCmd, []string{outDir, "WeatherForecaster"}); err != nil {
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

	err := NewCmd.RunE(NewCmd, []string{outDir, "bad_name_123"})
	if err == nil {
		t.Fatal("expected error for non-alpha block name, got nil")
	}
}
