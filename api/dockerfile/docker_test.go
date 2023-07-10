package dockerfile

import (
	"fmt"
	"io/ioutil"
	"os"
	"regexp"
	"testing"
)

func assertEqual(t *testing.T, a interface{}, b interface{}) {
	if a != b {
		t.Fatalf("%s != %s", a, b)
	}
}

func setVersion() error {
	path := "../../python/clay/__version__.py"
	contents, err := ioutil.ReadFile(path)
	if err != nil {
		fmt.Printf("Error reading file: %v", err)
		return err
	}

	versionString := string(contents)
	re := regexp.MustCompile(`"([^"]*)"`)
	match := re.FindStringSubmatch(versionString)
	Version = match[1]
	fmt.Println("Clay Version: ", Version)
	return nil
}

// TODO: Write a much better and more comprehensive test
func TestGenerateDockerfile(t *testing.T) {
	setVersion()
	defer os.Remove("Dockerfile")
	configPath := "./_test_configs/test.yaml"

	err := GenerateDockerfile(configPath, "src", false)
	if err != nil {
		t.Errorf("Test failed: %s", err.Error())
	}
	err = GenerateDockerfile(configPath, "src", true)
	if err != nil {
		t.Errorf("Test failed: %s", err.Error())
	}
}

func TestGetBuildFromConfigFile(t *testing.T) {
	setVersion()
	configPath := "./_test_configs/test.yaml"
	build, err := getBuildFromConfigFile(configPath)
	assertEqual(t, build.PythonVersion, "3.10")
	assertEqual(t, build.Conda, false)
	assertEqual(t, build.Gdal, true)

	aptPackages := []string{"wget", "curl"}
	for i, pkg := range build.AptGet {
		assertEqual(t, pkg, aptPackages[i])
	}

	assertEqual(t, build.Requirements, "requirements.txt")
	fmt.Printf("%+v\n%+v", build, err)
}
