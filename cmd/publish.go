package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"time"

	"github.com/example/clay/pkg/config"
	"github.com/example/clay/pkg/registry"

	"github.com/spf13/cobra"
)

var (
	blockRegistryHost string
	dockerRegistry    string
	documentationURL  string
	thumbnailURL      string
)

func publishBlockToRegistryCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "publish",
		Short: "Publish the block to the Clay registry",
		Long:  "Build a Docker image, push it to the configured Docker registry, and then publish the block to the Clay registry.",
		RunE:  publishBlockCmd,
	}

	cmd.Flags().StringVar(&dockerRegistry, "docker-registry-host", "REDACTED.dkr.ecr.us-east-2.amazonaws.com", "If specified, the block's Docker image will be pushed to that registry. Otherwise, the default registry will be used")
	cmd.Flags().StringVar(&blockRegistryHost, "block-registry-host", "http://localhost:8080", "If specified, the block will be published to that registry. Otherwise, the default registry will be used.")
	cmd.Flags().StringVar(&documentationURL, "documentation-url", "", "If specified this can be used for block documentation")
	cmd.Flags().StringVar(&thumbnailURL, "thumbnail-url", "", "If specified this can be used for block thumbnail")

	return cmd
}

func publishBlockCmd(cmd *cobra.Command, args []string) error {
	cwd, err := os.Getwd()
	if err != nil {
		return err
	}

	cfg, err := config.GetConfig(cwd)
	if err != nil {
		return err
	}

	image := fmt.Sprintf("%s/%s:%s", dockerRegistry, cfg.Name, cfg.Version)

	// build image
	buildCmd := exec.Command("clay", "build", "-t", image)
	buildCmd.Stderr = os.Stderr
	buildCmd.Stdout = os.Stdout
	if err := buildCmd.Run(); err != nil {
		return err
	}

	// push image to docker registry
	pushCmd := exec.Command("clay", "push", image)
	pushCmd.Stderr = os.Stderr
	pushCmd.Stdout = os.Stdout
	if err := pushCmd.Run(); err != nil {
		return err
	}

	br := registry.NewBlockRegistry(blockRegistryHost, 5*time.Second)

	req, err := buildPublishBlockRequest(cfg, documentationURL, thumbnailURL, image)
	if err != nil {
		return err
	}

	//publish block to clay registry
	err = br.Publish(req)
	if err == registry.ErrAlreadyExists {
		return fmt.Errorf("block %s with version %s already exists, skipping the publish", req.Name, req.Version)
	}
	if err != nil {
		return err
	}

	fmt.Printf("🎉 block %s with version %s published successfully to clay registry\n", req.Name, req.Version)
	return nil
}

func buildPublishBlockRequest(cfg *config.Config, documentationURL, thumbnailURL, dockerImage string) (*registry.PublishBlockRequest, error) {
	buildJSON, err := json.Marshal(cfg.Bulid)
	if err != nil {
		return nil, fmt.Errorf("error while marshalling build json: %w", err)
	}

	req := &registry.PublishBlockRequest{
		Name:             cfg.Name,
		Kind:             cfg.Kind,
		Type:             cfg.Type,
		Version:          cfg.Version,
		DockerImage:      dockerImage,
		DocumentationURL: documentationURL,
		ThumbnailURL:     thumbnailURL,
		Specification: &registry.Specification{
			APIVersion: cfg.APIVersion,
			Title:      cfg.Name,
			Author:     cfg.Author,
			Tags:       cfg.Tags,
			Parameters: cfg.Parameters,
			Inputs:     cfg.Inputs,
			Outputs:    cfg.Outputs,
			Build:      buildJSON,
			ENV:        cfg.ENV,
			Gpu:        cfg.Gpu,
		},
	}

	return req, nil

}
