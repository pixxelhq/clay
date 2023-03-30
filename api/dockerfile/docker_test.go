package dockerfile

import (
	"fmt"
	"os"
	"testing"
)

func assertEqual(t *testing.T, a interface{}, b interface{}) {
	if a != b {
		t.Fatalf("%s != %s", a, b)
	}
}

// TODO: Write a much better and more comprehensive test
func TestGenerateDockerfile(t *testing.T) {
	defer os.Remove("Dockerfile")
	configPath := "./_test_configs/test.yaml"

	err := GenerateDockerfile(configPath, ".", false)
	if err != nil {
		t.Errorf("Test failed: %s", err.Error())
	}
	err = GenerateDockerfile(configPath, ".", true)
	if err != nil {
		t.Errorf("Test failed: %s", err.Error())
	}
}

func TestGetBuildFromConfigFile(t *testing.T) {
	configPath := "./_test_configs/test.yaml"
	build, err := getBuildFromConfigFile(configPath)
	assertEqual(t, build.PythonVersion, "3.9")
	assertEqual(t, build.Conda, true)
	assertEqual(t, build.Gdal, false)

	aptPackages := []string{"wget", "curl"}
	for i, pkg := range build.AptGet {
		assertEqual(t, pkg, aptPackages[i])
	}

	assertEqual(t, build.Requirements, "requirements-or-conda.yml")
	fmt.Printf("%+v\n%+v", build, err)
}
