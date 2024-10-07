//go:build docker_push_test

package docker

import (
	"fmt"
	"os/exec"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestDockerRegistry_PushImage(t *testing.T) {
	// Set up test environment
	imageName := "registry"
	tag := "latest"
	registryURI := "localhost:5001"

	// we are using the registry image as dummy image which will be pushed to local registry
	dpr, err := exec.Command("docker", "pull", "registry").CombinedOutput()
	assert.NoError(t, err, string(dpr))

	// Start the local Docker registry
	startRegistryCmd := exec.Command("docker", "run", "-d", "-p", "5001:5000", imageName)
	srr, err := startRegistryCmd.CombinedOutput()
	assert.NoError(t, err, fmt.Sprintf("failed to start local Docker registry, %s", string(srr)))
	t.Logf("this is the container id %q", string(srr))
	defer func() {
		resp, err := exec.Command("docker", "stop", strings.ReplaceAll(string(srr), "\n", "")).CombinedOutput()
		if err != nil {
			t.Logf("failed to stop local Docker registry, %s", string(resp))
		}
	}()

	dr := NewDockerRegistry(registryURI)
	err = dr.PushImage(imageName, tag)
	assert.NoError(t, err)

	// Cleanup
	deleteImageCmd := exec.Command("docker", "rmi", fmt.Sprintf("%s/%s:%s", registryURI, imageName, tag))
	dir, err := deleteImageCmd.CombinedOutput()
	assert.NoError(t, err, fmt.Sprintf("failed to delete test image, %s", string(dir)))

}
