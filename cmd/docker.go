package cmd

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/example/clay/pkg/config"
	"github.com/example/clay/pkg/docker"
	"github.com/spf13/cobra"
)

var (
	awsSecretID   string = "CODEARTIFACT_AUTH_TOKEN"
	awsSecretFile string = "CODEARTIFACT_AUTH_TOKEN.txt"

	dockerfilePath string
	buildTag       string
	buildNoCache   bool
	buildSecrets   []string
	buildArgs      []string
)

func buildDockerImageCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "build <command>",
		Short: "Build a dockerimage from dockerfile generated from /specifications/model_specification_dev.yaml if dockerfile path is not provided",
		RunE:  buildCmd,
	}

	cmd.Flags().StringVarP(&buildTag, "tag", "t", "", "Specify the name of the built image in the format 'repository:tag'")
	cmd.Flags().StringVarP(&dockerfilePath, "file", "f", "", "Specify the dockerfile path, if not provided clay will create one from specfile and use it")
	cmd.Flags().BoolVar(&buildNoCache, "no-cache", false, "When true do not use cache when building the image (Default: flase)")
	cmd.Flags().StringArrayVar(&buildSecrets, "secret", []string{}, `Secret to expose to the build (format:"id=mysecret[,src=/local/secret]")`)
	cmd.Flags().StringArrayVar(&buildArgs, "build-arg", []string{}, `Set build-time variables`)

	return cmd
}

func buildCmd(cmd *cobra.Command, args []string) error {
	cwd, err := os.Getwd()
	if err != nil {
		return err
	}

	cfg, err := config.GetConfig(cwd)
	if err != nil {
		return err
	}

	if buildTag == "" {
		buildTag = cfg.Name
	}

	if dockerfilePath == "" {
		var err error
		srcCodeDir := filepath.Base(cwd)
		dockerfilePath, err = getOrCreateDockerfile(srcCodeDir, cfg)
		if err != nil {
			return err
		}
	}

	//Generate AWS code artifact secret for downloaing clay python sdk
	// This should be removed once clay is open sourced.
	secretFile, err := generateAWSSecret()
	if err != nil {
		return err
	}
	defer os.Remove(secretFile.Name())

	//Set secret and build-arg for AWS secret
	buildSecrets = append(buildSecrets, fmt.Sprintf("id=%s,src=%s", awsSecretID, secretFile.Name()))

	err = docker.BuildImage(buildTag, dockerfilePath, buildSecrets, buildArgs, buildNoCache)
	if err != nil {
		return err
	}

	fmt.Printf("docker image %s has been built using %s", buildTag, dockerfilePath)

	return nil
}

func getOrCreateDockerfile(srcCodeDir string, cfg *config.Config) (string, error) {
	dockerfilePath, err := docker.GetDockerFile()
	if err == docker.ErrDoesNotExists {
		dockerfilePath, err = docker.CreateDockerFile(srcCodeDir, ".", cfg)
	}

	return dockerfilePath, err
}

func generateAWSSecret() (*os.File, error) {
	args := []string{}
	args = append(args, "codeartifact", "get-authorization-token",
		"--profile", "d-platform-services",
		"--domain", "REDACTED-ARTIFACTORY",
		"--domain-owner", "REDACTED-AWS-ACCT",
		"--query", "authorizationToken",
		"--region", "us-east-2",
		"--output", "text")

	outputFile, err := os.Create(awsSecretFile)
	if err != nil {
		return nil, fmt.Errorf("error while generating aws secret: %w", err)
	}
	defer outputFile.Close()

	awsGenerateSecretCmd := exec.Command("aws", args...)
	awsGenerateSecretCmd.Stdout = outputFile
	awsGenerateSecretCmd.Stderr = os.Stderr

	if err := awsGenerateSecretCmd.Run(); err != nil {
		return nil, err
	}

	return outputFile, nil
}
