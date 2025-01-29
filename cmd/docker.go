package cmd

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/MakeNowJust/heredoc"
	"github.com/example/clay/pkg/config"
	"github.com/example/clay/pkg/docker"
	"github.com/spf13/cobra"
)

var (
	awsSecretID   string = "CODEARTIFACT_AUTH_TOKEN"
	awsSecretFile string = ""

	dockerfilePath string
	buildTag       string
	buildNoCache   bool
	buildSecrets   []string
	buildArgs      []string
	platform       []string
)

// TODO: Refactor these commands into separate files with docker directory.
func buildDockerImageCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "build",
		Short:   "Build an image from clay.yaml, This command uses sudo to build docker image",
		Long:    "Build an image from clay.yaml. \nIf tag is not provided it will use `name` and `version` mentioned in the clay.yaml for image creation in the format `name:tag`",
		Example: "clay build -t tagName -f ./Dockerfile",
		RunE:    buildCmd,
	}

	cmd.Flags().StringVarP(&buildTag, "tag", "t", "", "Provide the build tag in the format 'repository:tag'. (Default: name:tag, `name` and `tag` mentioned in the clay.yaml config).")
	cmd.Flags().StringVarP(&dockerfilePath, "file", "f", "", "Provide the Dockerfile path. If not provided, Clay will create one using the configuration from clay.yaml.")
	cmd.Flags().BoolVar(&buildNoCache, "no-cache", false, "When set to true, caching will not be used when building the image. (Default: false)")
	cmd.Flags().StringArrayVar(&buildSecrets, "secret", []string{}, `Secret to expose to the build (format:"id=mysecret[,src=/local/secret]")`)
	cmd.Flags().StringArrayVar(&buildArgs, "build-arg", []string{}, `Set build-time variables`)
	cmd.Flags().StringArrayVar(&platform, "platform", []string{}, "Set target platform for build")

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

	return buildImage(cwd, cfg)
}

func buildImage(projectDir string, cfg *config.Config) error {
	if buildTag == "" {
		buildTag = fmt.Sprintf("%s:%s", cfg.Name, cfg.Version)
		fmt.Printf("No build tag provided. Using `name` and `version` from clay.yaml as the build tag: %s\n", buildTag)
	}

	if dockerfilePath == "" {
		var err error
		srcCodeDir := filepath.Base(projectDir)
		dockerfilePath, err = getOrCreateDockerfile(srcCodeDir, cfg)
		if err != nil {
			return err
		}
	}

	//Generate AWS code artifact secret for downloaing clay python sdk
	//This should be removed once clay is open sourced.
	secretFile, err := generateAWSSecret()
	if err != nil {
		return err
	}
	defer os.Remove(secretFile.Name())

	//Set secret and build-arg for AWS secret
	buildSecrets = append(buildSecrets, fmt.Sprintf("id=%s,src=%s", awsSecretID, secretFile.Name()))

	bf := docker.BuildFlags{
		Secrets:   buildSecrets,
		BuildArgs: buildArgs,
		NoCache:   buildNoCache,
		Platforms: platform,
	}
	err = docker.Build(buildTag, dockerfilePath, bf)
	if err != nil {
		return err
	}

	fmt.Printf("🎉 docker image %s has been built using %s \n", buildTag, dockerfilePath)
	return nil
}

func pushToDockerRegistryCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "push [IMAGE]",
		Short:   "Push the docker image to registry. This command uses sudo to build docker image",
		Long:    "Push the docker image to registry, if image is not provided, it will use `name` and `tag` mentioned in clay.yaml for image name in the format `name:tag`",
		Example: "clay push registry.io/testing-model:0.0.1",
		RunE:    pushCmd,
	}

	return cmd
}

func pushCmd(cmd *cobra.Command, args []string) error {
	cwd, err := os.Getwd()
	if err != nil {
		return err
	}

	cfg, err := config.GetConfig(cwd)
	if err != nil {
		return err
	}

	image := fmt.Sprintf("%s:%s", cfg.Name, cfg.Version)
	if len(args) > 0 {
		image = args[0]
	}
	if image == "" {
		return fmt.Errorf("no image name was provided in the arguments, and neither `name` nor `version` is set in the clay.yaml file. Please specify an image name or ensure the configuration is complete in clay.yaml")
	}

	fmt.Printf("🧐 Serching image %s \n", image)
	err = docker.ImageExists(image)
	if err == docker.ErrDoesNotExists {
		return fmt.Errorf("oops image %s does not exists. First build the image using `clay build` command to build this image", image)
	}
	if err != nil {
		return fmt.Errorf("error while searching image %s in docker image list: %w", image, err)
	}

	err = docker.Push(image)
	if err == docker.ErrDoesNotExists {
		return fmt.Errorf("image %s does not exists", image)
	}
	if err != nil {
		return err
	}

	fmt.Printf("🎉 docker image %s has been pushed to specified registry\n", image)
	return nil
}

func getOrCreateDockerfile(srcCodeDir string, cfg *config.Config) (string, error) {
	dockerfilePath, err := docker.GetDockerFile()
	if err == docker.ErrDoesNotExists {
		fmt.Printf("dockerfile does not exists in the %s. Creating one... \n ", srcCodeDir)
		dockerfilePath, err = docker.CreateDockerFile(srcCodeDir, ".", cfg)
	}

	return dockerfilePath, err
}

func generateAWSSecret() (*os.File, error) {
	args := []string{}
	args = append(args, "codeartifact", "get-authorization-token",
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
		defer os.Remove(outputFile.Name())
		return nil, err
	}

	return outputFile, nil
}

func runDockerImageCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "run [IMAGE NAME] [ARG...]",
		Short: "Run the docker image",
		Long: heredoc.Doc(
			"Run the docker image. You need to provide the image name which you want to run.\n"),
		Example: "clay run registry.io/testing-model:0.0.1",
		RunE:    runImage,
		Args:    cobra.MinimumNArgs(1),
	}

	return cmd
}

func runImage(cmd *cobra.Command, args []string) error {
	// assuming arg[0] will be image name and arg[1:] will and args
	image := args[0]
	cwd, err := os.Getwd()
	if err != nil {
		return err
	}

	cfg, err := config.GetConfig(cwd)
	if err != nil {
		return err
	}

	return docker.Run(image, args[1:], cfg)
}
