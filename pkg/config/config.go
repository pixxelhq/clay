package config

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/santhosh-tekuri/jsonschema/v6"
	"sigs.k8s.io/yaml"
)

const configFileName = "clay.yaml"

type Build struct {
	PythonVersion  string   `yaml:"python-version" json:"python-version"`
	Conda          bool     `yaml:"conda" json:"conda"`
	Gdal           bool     `yaml:"gdal" json:"gdal"`
	AptGetPkgs     []string `yaml:"apt-get" json:"apt-get"`
	DependencyFile string   `yaml:"requirements" json:"requirements"`
}

type Config struct {
	APIVersion string          `yaml:"apiVersion" json:"apiVersion"`
	Kind       string          `yaml:"kind" json:"kind"`
	Type       string          `yaml:"type" json:"type"`
	Name       string          `yaml:"name" json:"name"`
	Version    string          `yaml:"version" json:"version"`
	Author     string          `yaml:"author" json:"author"`
	Tags       []string        `yaml:"tags" json:"tags"`
	Parameters json.RawMessage `yaml:"parameters" json:"parameters"`
	Inputs     json.RawMessage `yaml:"inputs" json:"inputs"`
	Outputs    json.RawMessage `yaml:"outputs" json:"outputs"`
	ENV        json.RawMessage `yaml:"env" json:"env"`
	Bulid      *Build          `yaml:"build" json:"build"`
	Gpu        bool            `yaml:"gpu" json:"gpu"`
}

func GetConfig(projectDir string) (*Config, error) {
	configFilePath, err := getConfigFilePath(projectDir)
	if err != nil {
		return nil, err
	}

	data, err := os.ReadFile(configFilePath)
	if err != nil {
		return nil, err
	}

	dataJSON, err := yaml.YAMLToJSON(data)
	if err != nil {
		return nil, fmt.Errorf("%s is not valid YAML: %w\nhint: check the indentation and quotes at the line named above", configFilePath, err)
	}

	doc, err := jsonschema.UnmarshalJSON(bytes.NewReader(dataJSON))
	if err != nil {
		return nil, fmt.Errorf("%s could not be read: %w", configFilePath, err)
	}
	if err := validate(doc); err != nil {
		return nil, err
	}

	config := &Config{}
	if err := json.Unmarshal(dataJSON, config); err != nil {
		return nil, fmt.Errorf("%s could not be read: %w", configFilePath, err)
	}

	return config, nil
}

func getConfigFilePath(projectDir string) (string, error) {
	configFilePath := filepath.Join(projectDir, configFileName) // assuming that scaffholding code has source
	_, err := os.Stat(configFilePath)
	if os.IsNotExist(err) {
		return "", fmt.Errorf("no %s in %s\nhint: run clay in the block's project folder, or create a block with 'clay new <path>'", configFileName, projectDir)
	}
	if err != nil {
		return "", err
	}

	return configFilePath, nil
}
