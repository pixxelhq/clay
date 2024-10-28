package config

import (
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v2"
)

type Build struct {
	PythonVersion  string   `yaml:"python-version"`
	Conda          bool     `yaml:"conda"`
	AptGetPkgs     []string `yaml:"apt-get"`
	DependencyFile string   `yaml:"requirements"`
}

type Config struct {
	Name    string `yaml:"name"`
	Version string `yaml:"version"`
	Bulid   *Build `yaml:"build"`
}

func GetConfig(projectDir string) (*Config, error) {
	specfilePath, err := getSpecfilePath(projectDir)
	if err != nil {
		return nil, err
	}

	data, err := os.ReadFile(specfilePath)
	if err != nil {
		return nil, err
	}

	config := &Config{}
	err = yaml.Unmarshal(data, config)
	if err != nil {
		return nil, err
	}

	return config, nil
}

func getSpecfilePath(projectDir string) (string, error) {
	specFileName := "model_specification_dev.yaml"                                                                         //once clay.yaml is introduced, that clay.yaml config file should be used.
	specfilePath := filepath.Join(projectDir, filepath.Base(projectDir), "specifications", "model_specification_dev.yaml") // assuming that scaffholding code has source
	_, err := os.Stat(specfilePath)
	if os.IsNotExist(err) {
		return "", fmt.Errorf("🙅‍♂️ %s file does not exist in: %s, please try to run the command in the root folder of the project", specFileName, projectDir)
	}
	if err != nil {
		return "", err
	}

	return specfilePath, nil
}
