package dockerfile

import (
	"os"

	"github.com/example/orchestrator/core/block"
	"sigs.k8s.io/yaml"
)

type Environment struct {
	Environment block.Build `json:"build"`
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
