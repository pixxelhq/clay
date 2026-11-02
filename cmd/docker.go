package cmd

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/MakeNowJust/heredoc"
	"github.com/pixxelhq/clay/pkg/blockname"
	"github.com/pixxelhq/clay/pkg/config"
	"github.com/pixxelhq/clay/pkg/docker"
	"github.com/spf13/cobra"
)

var (
	dockerfilePath string
	buildTag       string
	buildNoCache   bool
	buildSecrets   []string
	buildArgs      []string
	platform       []string
	envVars        []string
	inputJSON      string
	inputURI       string
)

// TODO: Refactor these commands into separate files with docker directory.
func buildDockerImageCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "build",
		Short:   "Build a Docker image from clay.yaml",
		Long:    "Build a Docker image from clay.yaml.\nIf --tag is not provided, the image is tagged as `<name>:<version>` using the values from clay.yaml.",
		Example: "clay build --tag my-block:0.1.0 --file ./Dockerfile",
		RunE:    buildCmd,
	}

	cmd.Flags().StringVarP(&buildTag, "tag", "t", "", "Provide the build tag in the format 'repository:tag'. (Default: `<name>:<version>` from clay.yaml)")
	cmd.Flags().StringVarP(&dockerfilePath, "file", "f", "", "Provide the Dockerfile path. If not provided, Clay generates one from clay.yaml on each build (see 'clay dockerfile').")
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

	_, err = buildImage(cwd, cfg, buildTag)
	return err
}

// buildImage builds the block's docker image and returns the resolved tag
// (either the tag argument, or a "<name>:<version>" default derived from the
// project config). Callers pass in the desired tag explicitly — the function
// does not read or mutate the `buildTag` package-level variable — so that
// both CLI (`clay build`) and programmatic callers (`clay publish`) behave
// predictably.
func buildImage(projectDir string, cfg *config.Config, tag string) (string, error) {
	if err := docker.CheckDaemon(); err != nil {
		return "", err
	}

	if tag == "" {
		tag = fmt.Sprintf("%s:%s", cfg.Name, cfg.Version)
		fmt.Printf("No build tag provided. Using `name` and `version` from clay.yaml as the build tag: %s\n", tag)
	}

	dockerfile := dockerfilePath
	if dockerfile == "" {
		warnLegacyDockerfile(projectDir)

		tmpDir, err := os.MkdirTemp("", "clay-build-")
		if err != nil {
			return "", err
		}
		defer os.RemoveAll(tmpDir)

		dockerfile, err = generateDockerfile(projectDir, tmpDir, cfg)
		if err != nil {
			return "", err
		}
	}

	bf := docker.BuildFlags{
		Secrets:   buildSecrets,
		BuildArgs: buildArgs,
		NoCache:   buildNoCache,
		Platforms: platform,
	}
	fmt.Printf("🔨 Building docker image %s\n", tag)
	if err := docker.Build(tag, dockerfile, bf); err != nil {
		return "", err
	}

	if dockerfilePath == "" {
		fmt.Printf("🎉 docker image %s has been built using a Dockerfile generated from clay.yaml\n", tag)
	} else {
		fmt.Printf("🎉 docker image %s has been built using %s\n", tag, dockerfilePath)
	}
	return tag, nil
}

// warnLegacyDockerfile warns when the project has a Dockerfile that an older
// Clay version wrote. clay build and clay publish no longer read it unless
// -f names it.
func warnLegacyDockerfile(projectDir string) {
	if _, err := os.Stat(filepath.Join(projectDir, "Dockerfile")); err != nil {
		return
	}
	fmt.Fprintln(os.Stderr, "warning: ./Dockerfile is not used. Clay generates the Dockerfile from clay.yaml on each build.\n"+
		"To build with your Dockerfile, pass `-f Dockerfile`. Otherwise, delete it.")
}

func pushToDockerRegistryCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "push [image]",
		Short:   "Push a built Docker image to a Docker registry",
		Long:    "Push a Docker image to the Docker registry.\nIf [image] is not provided, it defaults to `<name>:<version>` from clay.yaml.",
		Example: "clay push registry.example.com/my-block:0.1.0",
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

	if err := docker.CheckDaemon(); err != nil {
		return err
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

func packageDir(projectDir string, cfg *config.Config) (string, error) {
	candidates := []string{filepath.Base(projectDir)}
	if names, err := blockname.Parse(cfg.Name); err == nil {
		candidates = append([]string{names.Module}, candidates...)
	}
	for _, c := range candidates {
		if _, err := os.Stat(filepath.Join(projectDir, c, "entry.py")); err == nil {
			return c, nil
		}
	}
	return "", fmt.Errorf("no block package in %s: expected %s/entry.py", projectDir, candidates[0])
}

// generateDockerfile writes the Dockerfile generated from clay.yaml to
// outputDir and returns its path.
func generateDockerfile(projectDir, outputDir string, cfg *config.Config) (string, error) {
	srcCodeDir, err := packageDir(projectDir, cfg)
	if err != nil {
		return "", err
	}
	return docker.CreateDockerFile(srcCodeDir, outputDir, cfg)
}

func printDockerfileCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "dockerfile",
		Short: "Print the Dockerfile that clay build generates",
		Long: heredoc.Doc(`
			Print the Dockerfile that clay build generates from clay.yaml.

			To customize it, save the output and build with -f.
		`),
		Example: heredoc.Doc(`
			clay dockerfile > Dockerfile
			clay build -f Dockerfile
		`),
		Args: cobra.NoArgs,
		RunE: printDockerfile,
	}
}

func printDockerfile(cmd *cobra.Command, args []string) error {
	cwd, err := os.Getwd()
	if err != nil {
		return err
	}

	cfg, err := config.GetConfig(cwd)
	if err != nil {
		return err
	}

	srcCodeDir, err := packageDir(cwd, cfg)
	if err != nil {
		return err
	}
	return docker.RenderDockerfile(cmd.OutOrStdout(), srcCodeDir, cfg)
}

func runDockerImageCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "run <image> [args...]",
		Short: "Run a block's Docker image locally",
		Long: heredoc.Doc(`
			Run a block's Docker image locally.

			<image> is the Docker image to run. Any trailing [args...] are passed
			through to the container's entrypoint.
		`),
		Example: `clay run my-block:0.1.0 --input '[{"name":"raster","value":"s3://..."}]'`,
		RunE:    runImage,
		Args:    cobra.MinimumNArgs(1),
	}

	cmd.Flags().StringArrayVarP(&envVars, "env", "e", []string{}, "Set environment variables (format: KEY=VALUE)")
	cmd.Flags().StringVar(&inputJSON, "input", "", "JSON input array to pass to the block")
	cmd.Flags().StringVar(&inputURI, "input-uri", "", "URI to input JSON (e.g. s3://bucket/path/input.json)")

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

	if err := docker.CheckDaemon(); err != nil {
		return err
	}

	// Pass --input / --input-uri flags through to the container entrypoint
	containerArgs := args[1:]
	if inputJSON != "" {
		containerArgs = append(containerArgs, "--input", inputJSON)
	}
	if inputURI != "" {
		containerArgs = append(containerArgs, "--input-uri", inputURI)
	}

	return docker.Run(image, containerArgs, envVars, cfg)
}
