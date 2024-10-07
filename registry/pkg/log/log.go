package log

import (
	"fmt"
	"os"

	"github.com/rs/zerolog"
)

var logger = zerolog.New(os.Stderr).With().Timestamp().Caller().Logger().Level(zerolog.ErrorLevel)

func InitLogger(level string) error {
	l, err := zerolog.ParseLevel(level)
	if err != nil {
		return err
	}

	logger = zerolog.New(os.Stderr).With().Timestamp().Caller().Logger().Level(l)
	return nil
}

func SetLogLevel(level zerolog.Level) {
	zerolog.SetGlobalLevel(level)
}

func Debug(args ...interface{}) {
	Print(zerolog.DebugLevel, args...)
}

func Info(args ...interface{}) {
	Print(zerolog.InfoLevel, args...)
}

func Warn(args ...interface{}) {
	Print(zerolog.WarnLevel, args...)
}

func Error(args ...interface{}) {
	Print(zerolog.ErrorLevel, args...)
}

func Fatal(args ...interface{}) {
	Print(zerolog.FatalLevel, args...)
}

func Debugf(format string, args ...interface{}) {
	Printf(zerolog.DebugLevel, format, args...)
}

func Infof(format string, args ...interface{}) {
	Printf(zerolog.InfoLevel, format, args...)
}

func Warnf(format string, args ...interface{}) {
	Printf(zerolog.WarnLevel, format, args...)
}

func Errorf(format string, args ...interface{}) {
	Printf(zerolog.ErrorLevel, format, args...)
}

func Fatalf(format string, args ...interface{}) {
	Printf(zerolog.FatalLevel, format, args...)
}

func Print(level zerolog.Level, args ...interface{}) {
	l := logger.GetLevel()
	logger.WithLevel(l).Msg(fmt.Sprint(args...))
}

func Printf(level zerolog.Level, format string, v ...interface{}) {
	l := logger.GetLevel()
	logger.WithLevel(l).Msgf(format, v...)
}
