package config

import (
	"github.com/mcuadros/go-defaults"
	"github.com/spf13/viper"
)

type Config struct {
	HTTPPort int `default:"8080" mapstructure:"HTTP_SERVER_PORT"`

	DBPassword      string `default:"postgres"                        mapstructure:"DB_PASSWORD"`
	DBUserName      string `default:"postgres"                        mapstructure:"DB_USERNAME"`
	DBHost          string `default:"localhost"                       mapstructure:"DB_HOST"`
	DBPort          int    `default:"5432"                            mapstructure:"DB_PORT"`
	DBName          string `default:"clay_registry_dev"               mapstructure:"DB_NAME"`
	DBMigrationPath string `default:"file://internal/store/migration" mapstructure:"DB_MIGRATION_PATH"`

	LogLevel string `default:"info" mapstructure:"LOG_LEVEL"`
}

// nolint
var App Config

func Load() error {
	viper.AddConfigPath("./")
	viper.AddConfigPath("../")
	viper.AddConfigPath("../../")
	viper.SetConfigName("app")
	viper.SetConfigType("env")

	viper.AutomaticEnv()

	if err := viper.ReadInConfig(); err != nil {
		return err
	}

	defaults.SetDefaults(&App)

	return viper.Unmarshal(&App)
}
