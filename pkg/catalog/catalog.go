package catalog

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

const catalogFileName = "catalog.yaml"

// Catalog is a parsed catalog.yaml. Media is the one section Clay understands:
// a mapping of key to relative file path, whose values callers rewrite to the
// uploaded URLs. Every other top-level documentation section lands in Sections
// and is passed through untouched.
type Catalog struct {
	Media    map[string]string      `yaml:"media"`
	Sections map[string]interface{} `yaml:",inline"`
}

func Load(projectDir string) (*Catalog, error) {
	return LoadFile(filepath.Join(projectDir, catalogFileName))
}

func LoadFile(path string) (*Catalog, error) {
	if _, err := os.Stat(path); err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}

	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	c := &Catalog{}
	if err := yaml.Unmarshal(raw, c); err != nil {
		return nil, fmt.Errorf("error parsing %s: %w", filepath.Base(path), err)
	}

	return c, nil
}

func (c *Catalog) Bytes() ([]byte, error) {
	out, err := yaml.Marshal(c)
	if err != nil {
		return nil, fmt.Errorf("error serializing %s: %w", catalogFileName, err)
	}
	return out, nil
}

func (c *Catalog) JSON() ([]byte, error) {
	doc := make(map[string]interface{}, len(c.Sections)+1)
	for k, v := range c.Sections {
		doc[k] = v
	}
	if c.Media != nil {
		doc["media"] = c.Media
	}

	out, err := json.Marshal(doc)
	if err != nil {
		return nil, fmt.Errorf("error encoding %s to json: %w", catalogFileName, err)
	}
	return out, nil
}
