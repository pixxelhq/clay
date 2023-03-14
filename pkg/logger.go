package pkg

import (
	"io"
	"os"
	"path"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/pkgerrors"
	lumberjack "gopkg.in/natefinch/lumberjack.v2"
)

func getTimezoneUTC() time.Time {
	return time.Now().UTC()
}

type LogConfig struct {
	// Log to console
	EnableConsoleLogging bool

	//Custom io.Writer interfaces
	CustomWriters []io.Writer

	// Name of Logger
	LoggerName string

	// Name of application associated with the logger
	ModuleName string

	// Directory where the log files are to be stored.
	Directory string

	// Filename
	Filename string

	// MaxBackups the maximum number of rolled files to keep as backup. 0 to never
	// delete rolled files
	MaxBackups int

	//MaxSize the maximum size of the file before it gets rolled
	MaxSize int

	// MaxAge the max age (in 24 hour periods) to keep the rolled files. 0 to disable
	// deletion
	MaxAge int
}

type Logger struct {
	*zerolog.Logger
}

// lumberjack.Logger implements the io.Writer interface
func newRollingFile(config *LogConfig) io.Writer {
	return &lumberjack.Logger{
		Filename:   path.Join(config.Directory, config.Filename),
		MaxSize:    config.MaxSize,
		MaxAge:     config.MaxAge,
		MaxBackups: config.MaxBackups,
	}
}
func NewLogger(config *LogConfig) *Logger {
	var writers []io.Writer

	// setting global zerolog configs
	zerolog.SetGlobalLevel(zerolog.InfoLevel)
	zerolog.ErrorStackMarshaler = pkgerrors.MarshalStack
	zerolog.ErrorFieldName = "err"

	// setting timezone to IST
	zerolog.TimestampFunc = getTimezoneUTC

	// Logging to console, prettily,  if in `dev` env or it has been explicitly
	// enabled. Note this has a performance penalty

	if config.EnableConsoleLogging {
		writers = append(writers, os.Stdout)
	}

	// adding the rotating file writer
	writers = append(writers, newRollingFile(config))

	// Add any custom writers
	if len(config.CustomWriters) != 0 {
		writers = append(writers, config.CustomWriters...)
	}

	mw := zerolog.MultiLevelWriter(writers...)

	logger := zerolog.New(mw).With().Timestamp().Caller().Str("module_name", config.ModuleName).Str("logger_name", config.LoggerName).Logger()

	return &Logger{
		Logger: &logger,
	}
}
