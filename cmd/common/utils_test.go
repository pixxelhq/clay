package common

import "testing"

func TestIsValidVersion(t *testing.T) {
	tests := []struct {
		version string
		want    bool
	}{
		{"v1.0.0", true},
		{"v0.0.1", true},
		{"v1.2.3-rc.1", true},
		{"v1.2.3+build.5", true},
		{"1.0.0", false},
		{"v1", true},
		{"v1.0", true},
		{"not-a-version", false},
		{"", false},
	}

	for _, tt := range tests {
		t.Run(tt.version, func(t *testing.T) {
			if got := IsValidVersion(tt.version); got != tt.want {
				t.Errorf("IsValidVersion(%q) = %v, want %v", tt.version, got, tt.want)
			}
		})
	}
}

func TestGetlogger(t *testing.T) {
	logger := Getlogger()
	if logger == nil {
		t.Fatal("Getlogger() returned nil")
	}
}
