package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/pixxelhq/clay-framework/pkg/catalog"
	"github.com/pixxelhq/clay-framework/pkg/config"
	"github.com/pixxelhq/clay-framework/pkg/docker"
	"github.com/pixxelhq/clay-framework/pkg/registry"

	"github.com/spf13/cobra"
)

var (
	clayRegistry     string
	dockerRegistry   string
	documentationURL string
	thumbnailURL     string
)

func publishBlockToRegistryCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "publish",
		Short:   "Publish the block to the Clay registry",
		Long:    "Build a Docker image, push it to the configured Docker registry, and then publish the block to the Clay registry.",
		Example: "clay publish --docker-registry registry.example.com --clay-registry https://clay.example.com",
		PreRunE: func(cmd *cobra.Command, args []string) error {
			if dockerRegistry == "" {
				if dockerRegistry = os.Getenv("CLAY_DOCKER_REGISTRY"); dockerRegistry == "" {
					return fmt.Errorf("--docker-registry is required (or set CLAY_DOCKER_REGISTRY env var)")
				}
			}
			if clayRegistry == "" {
				if clayRegistry = os.Getenv("CLAY_REGISTRY_HOST"); clayRegistry == "" {
					return fmt.Errorf("--clay-registry is required (or set CLAY_REGISTRY_HOST env var)")
				}
			}
			return nil
		},
		RunE: publishBlockCmd,
	}

	cmd.Flags().StringVar(&dockerRegistry, "docker-registry", "", "Docker image registry URL (env: CLAY_DOCKER_REGISTRY)")
	cmd.Flags().StringVar(&clayRegistry, "clay-registry", "", "Clay block registry URL (env: CLAY_REGISTRY_HOST)")
	cmd.Flags().StringVar(&documentationURL, "documentation-url", "", "URL for block documentation")
	cmd.Flags().StringVar(&thumbnailURL, "thumbnail-url", "", "URL for block thumbnail")

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

	cat, err := catalog.Load(cwd)
	if err != nil {
		return err
	}

	image := fmt.Sprintf("%s/%s:%s", dockerRegistry, cfg.Name, cfg.Version)

	// Build the docker image. Pass the fully-qualified image (including the
	// docker registry host) as the tag so the build output is directly
	// pushable without re-tagging.
	builtTag, err := buildImage(cwd, cfg, image)
	if err != nil {
		return err
	}

	// Push image to docker registry
	if err := docker.Push(builtTag); err != nil {
		return fmt.Errorf("failed to push image %s: %w", builtTag, err)
	}
	fmt.Printf("🎉 docker image %s has been pushed to the registry\n", builtTag)

	var catalogJSON json.RawMessage
	if cat != nil {
		catalogJSON, err = cat.JSON()
		if err != nil {
			return err
		}
	}

	r := registry.New(clayRegistry, 5*time.Second)

	req, err := buildPublishBlockRequest(cfg, documentationURL, thumbnailURL, builtTag, catalogJSON)
	if err != nil {
		return err
	}

	//publish block to clay registry
	err = r.Publish(req)
	if err == registry.ErrAlreadyExists {
		return fmt.Errorf("block %s with version %s already exists, skipping the publish", req.Name, req.Version)
	}
	if err != nil {
		return err
	}

	fmt.Printf("🎉 block %s with version %s published successfully to clay registry\n", req.Name, req.Version)
	return nil
}

func buildPublishBlockRequest(cfg *config.Config, documentationURL, thumbnailURL, dockerImage string, catalogJSON json.RawMessage) (*registry.PublishBlockRequest, error) {
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
		Catalog: catalogJSON,
	}

	return req, nil

}
