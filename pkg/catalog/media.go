package catalog

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func IsRemoteURL(v string) bool {
	return strings.HasPrefix(v, "http://") || strings.HasPrefix(v, "https://")
}

// ResolvePath validates that rel is a safe, existing, readable regular file
// contained within root, and returns its absolute path. It rejects absolute
// paths, ".." escapes, and symlinks that resolve outside root, so a media:
// entry can never reach files outside the model repo.
func ResolvePath(root, rel string) (string, error) {
	if strings.TrimSpace(rel) == "" {
		return "", fmt.Errorf("path must not be empty")
	}
	if filepath.IsAbs(rel) {
		return "", fmt.Errorf("path %q must be relative to the model repo, not absolute", rel)
	}

	clean := filepath.Clean(rel)
	if clean == ".." || strings.HasPrefix(clean, ".."+string(os.PathSeparator)) {
		return "", fmt.Errorf("path %q escapes the model repo root", rel)
	}

	rootAbs, err := filepath.Abs(root)
	if err != nil {
		return "", err
	}
	fullAbs := filepath.Join(rootAbs, clean)

	if !within(rootAbs, fullAbs) {
		return "", fmt.Errorf("path %q escapes the model repo root", rel)
	}

	// Resolve symlinks and re-check containment, so a symlink inside the repo
	// can't point outside it. This also surfaces missing files.
	resolved, err := filepath.EvalSymlinks(fullAbs)
	if err != nil {
		if os.IsNotExist(err) {
			return "", fmt.Errorf("declared file %q does not exist", rel)
		}
		return "", fmt.Errorf("declared file %q is not accessible: %w", rel, err)
	}
	if rootResolved, err := filepath.EvalSymlinks(rootAbs); err == nil {
		if !within(rootResolved, resolved) {
			return "", fmt.Errorf("path %q resolves (via symlink) outside the model repo root", rel)
		}
	}

	info, err := os.Stat(fullAbs)
	if err != nil {
		return "", fmt.Errorf("declared file %q is not accessible: %w", rel, err)
	}
	if info.IsDir() {
		return "", fmt.Errorf("declared path %q is a directory, expected a file", rel)
	}

	return fullAbs, nil
}

// within reports whether child is root or sits inside root.
func within(root, child string) bool {
	rel, err := filepath.Rel(root, child)
	if err != nil {
		return false
	}
	return rel != ".." && !strings.HasPrefix(rel, ".."+string(os.PathSeparator))
}
