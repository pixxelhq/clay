package cmd

import (
	"io"
	"os"
	"strings"
	"testing"
)

func captureStdout(t *testing.T, fn func()) string {
	t.Helper()
	orig := os.Stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("pipe: %v", err)
	}
	os.Stdout = w

	fn()

	if err := w.Close(); err != nil {
		t.Fatalf("close: %v", err)
	}
	os.Stdout = orig

	data, err := io.ReadAll(r)
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	return string(data)
}

func TestVersionCmd_Metadata(t *testing.T) {
	cmd := VersionCmd()
	if cmd.Use != "version" {
		t.Errorf("Use = %q, want %q", cmd.Use, "version")
	}
	if cmd.RunE == nil {
		t.Fatal("RunE should not be nil")
	}
}

func TestVersionCmd_PrintsVersionWhenSet(t *testing.T) {
	t.Cleanup(func() { Version = "" })
	Version = "v1.2.3"

	cmd := VersionCmd()
	out := captureStdout(t, func() {
		if err := cmd.RunE(cmd, nil); err != nil {
			t.Fatalf("RunE returned error: %v", err)
		}
	})

	if !strings.Contains(out, "clay version v1.2.3") {
		t.Errorf("expected version output, got %q", out)
	}
}

func TestVersionCmd_PrintsFallbackWhenUnset(t *testing.T) {
	t.Cleanup(func() { Version = "" })
	Version = ""

	cmd := VersionCmd()
	out := captureStdout(t, func() {
		if err := cmd.RunE(cmd, nil); err != nil {
			t.Fatalf("RunE returned error: %v", err)
		}
	})

	if !strings.Contains(out, "Version information not available") {
		t.Errorf("expected fallback output, got %q", out)
	}
}
