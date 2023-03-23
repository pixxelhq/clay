package logger

import (
	"bytes"
	"io"
	"os"
	"strings"
	"testing"
)

func TestNewLogger(t *testing.T) {

	var testBuffer bytes.Buffer

	logger := NewLogger(&LogConfig{
		EnableConsoleLogging: true,
		LoggerName:           "testLogger",
		ModuleName:           "testModule",
		Directory:            "",
		Filename:             "testmodule.logs.txt",
		MaxBackups:           0,
		MaxSize:              512,
		MaxAge:               0,
		CustomWriters:        []io.Writer{&testBuffer},
	})

	logger.Info().Msg("testing")

	_, err := os.Stat("testmodule.logs.txt")

	if err != nil {
		t.Errorf("Test failed: %s", err.Error())
	}
	dataBytes, _ := os.ReadFile("testmodule.logs.txt")
	data := strings.Split(string(dataBytes), "\n")
	lastEntry := data[len(data)-2]
	bufferEntry := strings.Trim(testBuffer.String(), "\n")
	if lastEntry != bufferEntry {
		t.Errorf("Log mismatch: %s / %s", lastEntry, bufferEntry)
	}
	_ = os.Remove("testmodule.logs.txt")
}
