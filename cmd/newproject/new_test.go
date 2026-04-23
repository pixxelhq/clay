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

	flag := NewCmd.Flags().Lookup("readme-template")
	if flag == nil {
		t.Fatal("expected --readme-template flag to be registered")
	}
	if flag.DefValue != "false" {
		t.Errorf("readme-template default = %q, want %q", flag.DefValue, "false")
	}
}

func TestNewCmd_RunEScaffoldsProject(t *testing.T) {
	outDir := t.TempDir()
	t.Cleanup(func() { readmeTemplate = false })
	readmeTemplate = false

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
	t.Cleanup(func() { readmeTemplate = false })

	err := NewCmd.RunE(NewCmd, []string{outDir, "bad_name_123"})
	if err == nil {
		t.Fatal("expected error for non-alpha block name, got nil")
	}
}

func TestNewCmd_ReadmeTemplateFlagTogglesStub(t *testing.T) {
	outDir := t.TempDir()
	t.Cleanup(func() { readmeTemplate = false })

	if err := NewCmd.ParseFlags([]string{"--readme-template"}); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}
	if !readmeTemplate {
		t.Fatal("--readme-template should set readmeTemplate=true")
	}

	if err := NewCmd.RunE(NewCmd, []string{outDir, "AwesomeBlock"}); err != nil {
		t.Fatalf("RunE returned error: %v", err)
	}

	readme := filepath.Join(outDir, "awesome_block", "docs", "README.md")
	data, err := os.ReadFile(readme)
	if err != nil {
		t.Fatalf("expected catalog README stub at %q: %v", readme, err)
	}
	if len(data) == 0 {
		t.Error("expected non-empty catalog README stub")
	}
}
