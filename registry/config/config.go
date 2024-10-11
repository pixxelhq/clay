package config

import (
	"github.com/mcuadros/go-defaults"
	"github.com/spf13/viper"
)

type Config struct {
	HttpPort int `mapstructure:"HTTP_SERVER_PORT" default:"8080"`

	DBPassword      string `mapstructure:"DB_PASSWORD" default:"postgres"`
	DBUserName      string `mapstructure:"DB_USERNAME" default:"postgres"`
	DBHost          string `mapstructure:"DB_HOST" default:"localhost"`
	DBPort          int    `mapstructure:"DB_PORT" default:"5432"`
	DBName          string `mapstructure:"DB_NAME" default:"clay_registry_dev"`
	DBMigrationPath string `mapstructure:"DB_MIGRATION_PATH" default:"file://internal/store/migration"`

	LogLevel string `mapstructure:"LOG_LEVEL" default:"info"`
}

var App Config

func Load() error {
	viper.AddConfigPath("./")
	viper.AddConfigPath("../")
	viper.AddConfigPath("../../")
	viper.SetConfigName("app")
	viper.SetConfigType("env")

	viper.AutomaticEnv()

	err := viper.ReadInConfig()
	if err != nil {
		return err
	}

	defaults.SetDefaults(&App)
	return viper.Unmarshal(&App)

}
