//go:build integration

package docker

import (
	"fmt"
	"os/exec"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestPush(t *testing.T) {
	// Set up test environment
	buildtag := "registry:latest"
	registryURI := "localhost:5001"
	image := registryURI + "/" + buildtag

	// we are using the registry image as dummy image which will be pushed to local registry
	dpr, err := exec.Command("docker", "pull", buildtag).CombinedOutput()
	assert.NoError(t, err, string(dpr))

	// Start the local Docker registry
	startRegistryCmd := exec.Command("docker", "run", "-d", "-p", "5001:5000", buildtag)
	srcOutput, err := startRegistryCmd.CombinedOutput()
	assert.NoError(t, err, fmt.Sprintf("failed to start local Docker registry, %s", string(srcOutput)))
	t.Logf("this is the container id %q", string(srcOutput))
	defer func() {
		resp, err := exec.Command("docker", "stop", strings.ReplaceAll(string(srcOutput), "\n", "")).CombinedOutput()
		if err != nil {
			t.Logf("failed to stop local Docker registry, %s", string(resp))
		}
	}()

	//tag the image
	tagCmd := exec.Command("docker", "tag", buildtag, image)
	tagOutput, err := tagCmd.CombinedOutput()
	assert.NoError(t, err, fmt.Sprintf("failed to start local Docker registry, %s", string(tagOutput)))

	err = Push(image)
	assert.NoError(t, err)

	// Cleanup
	deleteImageCmd := exec.Command("docker", "rmi", image)
	dir, err := deleteImageCmd.CombinedOutput()
	assert.NoError(t, err, fmt.Sprintf("failed to delete test image, %s", string(dir)))

}
