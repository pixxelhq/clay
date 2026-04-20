package cmd

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestResolveParseSpec(t *testing.T) {
	tests := []struct {
		name           string
		spec           string
		uploadDir      string
		wantInputPath  string
		wantOutputPath string
	}{
		{
			name:           "explicit output",
			spec:           "block-README.md:parsed.md",
			uploadDir:      "catalog_readme",
			wantInputPath:  filepath.Join("catalog_readme", "block-README.md"),
			wantOutputPath: filepath.Join("catalog_readme", "parsed.md"),
		},
		{
			name:           "auto output",
			spec:           "README.md",
			uploadDir:      "docs",
			wantInputPath:  filepath.Join("docs", "README.md"),
			wantOutputPath: filepath.Join("docs", "README.parsed.md"),
		},
		{
			name:           "no extension",
			spec:           "Makefile",
			uploadDir:      "build",
			wantInputPath:  filepath.Join("build", "Makefile"),
			wantOutputPath: filepath.Join("build", "Makefile.parsed"),
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			input, output, err := resolveParseSpec(tt.spec, tt.uploadDir)
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if input != tt.wantInputPath {
				t.Errorf("input = %q, want %q", input, tt.wantInputPath)
			}
			if output != tt.wantOutputPath {
				t.Errorf("output = %q, want %q", output, tt.wantOutputPath)
			}
		})
	}
}

func TestResolveParseSpec_Errors(t *testing.T) {
	tests := []struct {
		name string
		spec string
	}{
		{name: "empty input", spec: ":output.md"},
		{name: "empty input no colon", spec: ""},
		{name: "empty output", spec: "input.md:"},
		{name: "absolute input", spec: "/etc/passwd"},
		{name: "traversal input", spec: "../secret.md"},
		{name: "absolute output", spec: "input.md:/etc/out"},
		{name: "traversal output", spec: "input.md:../out.md"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, _, err := resolveParseSpec(tt.spec, "dir")
			if err == nil {
				t.Errorf("expected error for spec %q, got nil", tt.spec)
			}
		})
	}
}

func TestParseTemplateFile(t *testing.T) {
	dir := t.TempDir()

	inputPath := filepath.Join(dir, "test.md")
	outputPath := filepath.Join(dir, "test.parsed.md")
	baseURL := "https://bucket.s3.us-east-1.amazonaws.com/blocks/foo/v1/docs"

	content := `# Test
![img]({{ addUrl "image.png" }})
Link: {{ addUrl "data/file.csv" }}
`
	if err := os.WriteFile(inputPath, []byte(content), 0644); err != nil {
		t.Fatal(err)
	}

	if err := parseTemplateFile(inputPath, outputPath, baseURL); err != nil {
		t.Fatalf("parseTemplateFile() error: %v", err)
	}

	got, err := os.ReadFile(outputPath)
	if err != nil {
		t.Fatalf("failed to read output: %v", err)
	}

	output := string(got)
	if !strings.Contains(output, baseURL+"/image.png") {
		t.Errorf("output missing resolved image URL, got:\n%s", output)
	}
	if !strings.Contains(output, baseURL+"/data/file.csv") {
		t.Errorf("output missing resolved CSV URL, got:\n%s", output)
	}
}

func TestParseTemplateFile_TrailingSlash(t *testing.T) {
	dir := t.TempDir()

	inputPath := filepath.Join(dir, "test.md")
	outputPath := filepath.Join(dir, "out.md")
	baseURL := "https://bucket.s3.us-east-1.amazonaws.com/prefix/"

	content := `{{ addUrl "file.txt" }}`
	if err := os.WriteFile(inputPath, []byte(content), 0644); err != nil {
		t.Fatal(err)
	}

	if err := parseTemplateFile(inputPath, outputPath, baseURL); err != nil {
		t.Fatalf("parseTemplateFile() error: %v", err)
	}

	got, err := os.ReadFile(outputPath)
	if err != nil {
		t.Fatal(err)
	}

	want := "https://bucket.s3.us-east-1.amazonaws.com/prefix/file.txt"
	if strings.TrimSpace(string(got)) != want {
		t.Errorf("got %q, want %q", strings.TrimSpace(string(got)), want)
	}
}

func TestParseTemplateFile_NoHTMLEscaping(t *testing.T) {
	dir := t.TempDir()

	inputPath := filepath.Join(dir, "test.md")
	outputPath := filepath.Join(dir, "out.md")
	baseURL := "https://bucket.s3.us-east-1.amazonaws.com/prefix"

	// Ampersands and angle brackets must NOT be HTML-escaped.
	content := `url: {{ addUrl "file.txt?a=1&b=2" }}
raw: <div>keep & preserve</div>
`
	if err := os.WriteFile(inputPath, []byte(content), 0644); err != nil {
		t.Fatal(err)
	}

	if err := parseTemplateFile(inputPath, outputPath, baseURL); err != nil {
		t.Fatalf("parseTemplateFile() error: %v", err)
	}

	got, err := os.ReadFile(outputPath)
	if err != nil {
		t.Fatal(err)
	}

	output := string(got)
	if strings.Contains(output, "&amp;") {
		t.Errorf("output contains HTML-escaped ampersand (&amp;), should use text/template:\n%s", output)
	}
	if strings.Contains(output, "&lt;") {
		t.Errorf("output contains HTML-escaped angle bracket (&lt;), should use text/template:\n%s", output)
	}
	if !strings.Contains(output, "a=1&b=2") {
		t.Errorf("output missing unescaped ampersand in URL:\n%s", output)
	}
	if !strings.Contains(output, "<div>keep & preserve</div>") {
		t.Errorf("output missing raw HTML content:\n%s", output)
	}
}

func TestParseTemplateFile_MissingInput(t *testing.T) {
	dir := t.TempDir()
	err := parseTemplateFile(filepath.Join(dir, "nonexistent.md"), filepath.Join(dir, "out.md"), "https://example.com")
	if err == nil {
		t.Error("expected error for missing input file, got nil")
	}
}
