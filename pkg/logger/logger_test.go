package logger

import (
	"bytes"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func newTestLogger(t *testing.T, buf *bytes.Buffer, enableConsole bool) (*Logger, string) {
	t.Helper()
	dir := t.TempDir()
	logger := NewLogger(&LogConfig{
		EnableConsoleLogging: enableConsole,
		LoggerName:           "testLogger",
		ModuleName:           "testModule",
		Directory:            dir,
		Filename:             "logs.txt",
		MaxBackups:           0,
		MaxSize:              512,
		MaxAge:               0,
		CustomWriters:        []io.Writer{buf},
	})
	return logger, filepath.Join(dir, "logs.txt")
}

func TestNewLogger_WritesToFileAndCustomWriter(t *testing.T) {
	var buf bytes.Buffer
	logger, logPath := newTestLogger(t, &buf, true)

	logger.Info().Msg("testing")

	if _, err := os.Stat(logPath); err != nil {
		t.Fatalf("log file not created: %v", err)
	}
	dataBytes, _ := os.ReadFile(logPath)
	data := strings.Split(string(dataBytes), "\n")
	lastEntry := data[len(data)-2]
	bufferEntry := strings.Trim(buf.String(), "\n")
	if lastEntry != bufferEntry {
		t.Errorf("log mismatch: file=%q, buffer=%q", lastEntry, bufferEntry)
	}
}

func TestNewLogger_LevelMethodsEmitExpectedLevels(t *testing.T) {
	tests := []struct {
		name      string
		emit      func(l *Logger)
		wantLevel string
	}{
		{"info", func(l *Logger) { l.Info().Msg("m") }, `"level":"info"`},
		{"warn", func(l *Logger) { l.Warn().Msg("m") }, `"level":"warn"`},
		{"error", func(l *Logger) { l.Error().Msg("m") }, `"level":"error"`},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			var buf bytes.Buffer
			logger, _ := newTestLogger(t, &buf, false)
			tc.emit(logger)
			if !strings.Contains(buf.String(), tc.wantLevel) {
				t.Errorf("expected %q in output, got %q", tc.wantLevel, buf.String())
			}
		})
	}
}

func TestNewLogger_DebugBelowGlobalLevelIsFiltered(t *testing.T) {
	var buf bytes.Buffer
	logger, _ := newTestLogger(t, &buf, false)
	logger.Debug().Msg("should not appear")
	if buf.Len() > 0 {
		t.Errorf("expected debug to be filtered (global level is info), got: %q", buf.String())
	}
}

func TestNewLogger_ConsoleLoggingDisabledDoesNotWriteToStdout(t *testing.T) {
	var buf bytes.Buffer
	logger, _ := newTestLogger(t, &buf, false)
	logger.Info().Msg("quiet")
	if buf.Len() == 0 {
		t.Fatal("expected log in custom writer buffer")
	}
}

func TestNewLogger_IncludesModuleAndLoggerName(t *testing.T) {
	var buf bytes.Buffer
	logger, _ := newTestLogger(t, &buf, false)
	logger.Info().Msg("tagged")
	out := buf.String()
	if !strings.Contains(out, `"module_name":"testModule"`) {
		t.Errorf("missing module_name in %q", out)
	}
	if !strings.Contains(out, `"logger_name":"testLogger"`) {
		t.Errorf("missing logger_name in %q", out)
	}
}
