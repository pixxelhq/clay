package dockerfile

import (
	"os"

	"github.com/example/orchestrator/core/v1alpha1/block"
	"sigs.k8s.io/yaml"
)

type Environment struct {
	Environment block.Build `json:"build"`
}

type Resource struct {
	Resource block.Runtime `json:"runtime_opts"`
}

func getBuildFromConfigFile(filename string) (block.Build, error) {
	// Read the YAML file
	data, err := os.ReadFile(filename)
	if err != nil {
		return block.Build{}, err
	}

	// Parse the YAML data into a Block struct
	var env Environment
	if err := yaml.Unmarshal(data, &env); err != nil {
		return block.Build{}, err
	}

	return env.Environment, nil
}

func getRuntimeOptsFromConfigFile(filename string) (block.Runtime, error) {
	// Read the YAML file
	data, err := os.ReadFile(filename)
	if err != nil {
		return block.Runtime{}, err
	}

	// Parse the YAML data into a Block struct
	var runtime Resource
	if err := yaml.Unmarshal(data, &runtime); err != nil {
		return block.Runtime{}, err
	}

	return runtime.Resource, nil
}
