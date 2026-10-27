package cmd

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/pixxelhq/clay/pkg/config"
)

func TestPackageDir(t *testing.T) {
	tests := []struct {
		name       string
		projectDir string // folder name of the project
		pkgDir     string // package folder inside it
		cfgName    string // name in clay.yaml
		want       string
	}{
		{"from clay.yaml name", "my-block", "my_block", "my-block", "my_block"},
		{"project folder renamed", "checkout-123", "my_block", "my-block", "my_block"},
		{"project made before the name rule", "my_block", "my_block", "myblock", "my_block"},
		{"no matching package folder", "some-dir", "other", "my-block", "some-dir"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			projectDir := filepath.Join(t.TempDir(), tt.projectDir)
			if err := os.MkdirAll(filepath.Join(projectDir, tt.pkgDir), 0755); err != nil {
				t.Fatalf("setup: %v", err)
			}
			got := packageDir(projectDir, &config.Config{Name: tt.cfgName})
			if got != tt.want {
				t.Errorf("packageDir() = %q, want %q", got, tt.want)
			}
		})
	}
}
