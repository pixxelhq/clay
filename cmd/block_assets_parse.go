package cmd

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"text/template"
)

// resolveParseSpec splits a --parse value into absolute input and output paths.
// The spec format is "<input>[:<output>]". Both paths are resolved relative to
// uploadDir. When no output is given, it defaults to <stem>.parsed<ext>.
func resolveParseSpec(spec, uploadDir string) (string, string, error) {
	parts := strings.SplitN(spec, ":", 2)
	input := parts[0]
	if input == "" {
		return "", "", fmt.Errorf("--parse: input filename must not be empty")
	}
	if err := validateParsePath("input", input); err != nil {
		return "", "", err
	}
	var output string
	if len(parts) == 2 {
		output = parts[1]
		if output == "" {
			return "", "", fmt.Errorf("--parse: output filename must not be empty when using <input>:<output> format")
		}
		if err := validateParsePath("output", output); err != nil {
			return "", "", err
		}
	} else {
		ext := filepath.Ext(input)
		stem := strings.TrimSuffix(input, ext)
		output = stem + ".parsed" + ext
	}
	return filepath.Join(uploadDir, input), filepath.Join(uploadDir, output), nil
}

// validateParsePath rejects absolute paths and any relative path that escapes
// the upload directory (e.g. "../x", "a/../../b"). Filenames that merely
// contain ".." as part of a name (e.g. "my..file.md") are allowed.
func validateParsePath(kind, p string) error {
	if filepath.IsAbs(p) {
		return fmt.Errorf("--parse: %s path %q must be a relative path within the upload directory", kind, p)
	}
	clean := filepath.Clean(p)
	if clean == ".." || strings.HasPrefix(clean, ".."+string(filepath.Separator)) {
		return fmt.Errorf("--parse: %s path %q must be a relative path within the upload directory", kind, p)
	}
	return nil
}

// parseTemplateFile renders inputPath through Go's text/template engine and
// writes the result to outputPath. The {{ addUrl "file" }} helper resolves
// relative asset references to <baseURL>/<file>. A temp file is used so that
// a failed render never leaves a partial output behind.
func parseTemplateFile(inputPath, outputPath, baseURL string) error {
	base := strings.TrimRight(baseURL, "/")
	funcMap := template.FuncMap{
		"addUrl": func(s string) string { return base + "/" + s },
	}

	tmpl, err := template.New(filepath.Base(inputPath)).
		Funcs(funcMap).
		ParseFiles(inputPath)
	if err != nil {
		return fmt.Errorf("failed to parse template %s: %w", inputPath, err)
	}

	tmp, err := os.CreateTemp(filepath.Dir(outputPath), ".parse-*")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	defer tmp.Close()
	defer os.Remove(tmpName)

	if err := tmpl.Execute(tmp, nil); err != nil {
		return fmt.Errorf("failed to execute template %s: %w", inputPath, err)
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	return os.Rename(tmpName, outputPath)
}
