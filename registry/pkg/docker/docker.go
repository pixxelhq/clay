package docker

import (
	"fmt"
	"os/exec"
)

type DockerRegistry struct {
	URI string
}

func NewDockerRegistry(registryURI string) *DockerRegistry {
	return &DockerRegistry{URI: registryURI}
}

func (dr *DockerRegistry) PushImage(imageName string, tag string) error {
	tagCmd := exec.Command("docker", "tag", imageName, fmt.Sprintf("%s/%s:%s", dr.URI, imageName, tag))
	if resp, err := tagCmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to tag image: %w, %s", err, string(resp))
	}

	pushCmd := exec.Command("docker", "push", fmt.Sprintf("%s/%s:%s", dr.URI, imageName, tag))
	if resp, err := pushCmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to push image: %w, %s", err, string(resp))
	}

	return nil
}
