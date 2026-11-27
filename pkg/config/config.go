package config

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"reflect"

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
	if fields, ok := doc.(map[string]any); ok && fields["apiVersion"] == apiVersionV1 {
		if err := validateV1(doc); err != nil {
			return nil, err
		}
	}

	config := &Config{}
	err = json.Unmarshal(dataJSON, config)
	var typeErr *json.UnmarshalTypeError
	if errors.As(err, &typeErr) {
		return nil, wrongTypeError(typeErr)
	}
	if err != nil {
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

func wrongTypeError(err *json.UnmarshalTypeError) error {
	expected := map[reflect.Kind]string{
		reflect.String: "text",
		reflect.Bool:   "true or false",
		reflect.Slice:  "a list",
		reflect.Struct: "a mapping",
		reflect.Map:    "a mapping",
	}[err.Type.Kind()]
	if expected == "" {
		expected = "a number"
	}
	found := map[string]string{
		"number": "a number",
		"string": "text",
		"bool":   "true or false",
		"array":  "a list",
		"object": "a mapping",
	}[err.Value]
	if found == "" {
		found = err.Value
	}
	hint := "see the clay.yaml reference: https://pixxelhq.github.io/clay/spec/"
	if err.Type.Kind() == reflect.String && err.Value == "number" {
		hint = "put the value in quotes so that YAML reads it as text"
	}
	subject := configFileName + ": " + err.Field
	if err.Field == "" {
		subject = configFileName
	}
	return fmt.Errorf("%s must be %s, not %s\nhint: %s", subject, expected, found, hint)
}
