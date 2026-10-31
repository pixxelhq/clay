package cmd

import (
	"os"
	"path/filepath"
	"strings"
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
		wantErr    bool
	}{
		{name: "from clay.yaml name", projectDir: "my-block", pkgDir: "my_block", cfgName: "my-block", want: "my_block"},
		{name: "project folder renamed", projectDir: "checkout-123", pkgDir: "my_block", cfgName: "my-block", want: "my_block"},
		{name: "project made before the name rule", projectDir: "my_block", pkgDir: "my_block", cfgName: "myblock", want: "my_block"},
		{name: "clay.yaml name changed", projectDir: "my-block", pkgDir: "my_block", cfgName: "weather-v2", wantErr: true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			projectDir := filepath.Join(t.TempDir(), tt.projectDir)
			if err := os.MkdirAll(filepath.Join(projectDir, tt.pkgDir), 0755); err != nil {
				t.Fatalf("setup: %v", err)
			}
			if err := os.WriteFile(filepath.Join(projectDir, tt.pkgDir, "entry.py"), nil, 0644); err != nil {
				t.Fatalf("setup: %v", err)
			}
			got, err := packageDir(projectDir, &config.Config{Name: tt.cfgName})
			if tt.wantErr {
				if err == nil || !strings.Contains(err.Error(), "expected weather_v2/entry.py") {
					t.Fatalf("packageDir() error = %v, want the no block package error", err)
				}
				return
			}
			if err != nil {
				t.Fatalf("packageDir() returned error: %v", err)
			}
			if got != tt.want {
				t.Errorf("packageDir() = %q, want %q", got, tt.want)
			}
		})
	}
}
