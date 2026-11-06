package cmd

import (
	"bytes"
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

// newBlockProject writes a minimal block project with the given python-version
// and returns its path.
func newBlockProject(t *testing.T, pythonVersion string) string {
	t.Helper()
	projectDir := filepath.Join(t.TempDir(), "my-block")
	if err := os.MkdirAll(filepath.Join(projectDir, "my_block"), 0755); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.WriteFile(filepath.Join(projectDir, "my_block", "entry.py"), nil, 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}
	writeClayYaml(t, projectDir, pythonVersion)
	return projectDir
}

func writeClayYaml(t *testing.T, projectDir, pythonVersion string) {
	t.Helper()
	spec := "name: my-block\nversion: 0.1.0\nbuild:\n  python-version: \"" + pythonVersion + "\"\n  requirements: requirements.txt\n"
	if err := os.WriteFile(filepath.Join(projectDir, "clay.yaml"), []byte(spec), 0644); err != nil {
		t.Fatalf("setup: %v", err)
	}
}

func readGeneratedDockerfile(t *testing.T, projectDir string) string {
	t.Helper()
	cfg, err := config.GetConfig(projectDir)
	if err != nil {
		t.Fatalf("GetConfig() returned error: %v", err)
	}
	path, err := generateDockerfile(projectDir, t.TempDir(), cfg)
	if err != nil {
		t.Fatalf("generateDockerfile() returned error: %v", err)
	}
	content, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read generated Dockerfile: %v", err)
	}
	return string(content)
}

func TestGenerateDockerfile_FollowsClayYaml(t *testing.T) {
	projectDir := newBlockProject(t, "3.10")

	first := readGeneratedDockerfile(t, projectDir)
	if !strings.Contains(first, "python3.10") {
		t.Fatalf("Dockerfile does not use python3.10:\n%s", first)
	}

	writeClayYaml(t, projectDir, "3.12")
	second := readGeneratedDockerfile(t, projectDir)
	if !strings.Contains(second, "python3.12") {
		t.Errorf("Dockerfile does not follow the changed python-version:\n%s", second)
	}

	if _, err := os.Stat(filepath.Join(projectDir, "Dockerfile")); !os.IsNotExist(err) {
		t.Errorf("a Dockerfile was written into the project (stat error: %v)", err)
	}
}

func TestPrintDockerfile_MatchesBuild(t *testing.T) {
	projectDir := newBlockProject(t, "3.11")
	wd, err := os.Getwd()
	if err != nil {
		t.Fatalf("setup: %v", err)
	}
	if err := os.Chdir(projectDir); err != nil {
		t.Fatalf("setup: %v", err)
	}
	t.Cleanup(func() { _ = os.Chdir(wd) })

	var out bytes.Buffer
	cmd := printDockerfileCmd()
	cmd.SetOut(&out)
	if err := cmd.RunE(cmd, nil); err != nil {
		t.Fatalf("clay dockerfile returned error: %v", err)
	}

	if want := readGeneratedDockerfile(t, projectDir); out.String() != want {
		t.Errorf("clay dockerfile output differs from the build Dockerfile\n got:\n%s\nwant:\n%s", out.String(), want)
	}
}
