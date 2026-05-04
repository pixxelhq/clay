package http

import (
	"fmt"
	"slices"

	"github.com/Masterminds/semver"
	rerr "github.com/pixxelhq/clay-framework/registry/pkg/error"
)

var (
	SupportedKind = []string{"block"}
	SupportedType = []string{"processing", "source", "visualization"}
)

func (s *Specification) Validate() error {
	if s.APIVersion == "" || s.Author == "" {
		return &rerr.RegistryError{
			Message: "specification: apiVersion and author can't be empty",
			Code:    rerr.ErrBadRequest,
		}
	}

	if s.Inputs == nil || s.Outputs == nil || s.Build == nil {
		return &rerr.RegistryError{
			Message: "specification: input, output and build fields can't be empty",
			Code:    rerr.ErrBadRequest,
		}
	}

	return nil
}

func (bcr *CreateBlockRequest) Validate() error {
	if bcr.Name == "" || bcr.Version == "" || bcr.DocumentationURL == "" || bcr.DockerImage == "" {
		return &rerr.RegistryError{
			Message: "name, version, docker_image and documentation_url can not be empty",
			Code:    rerr.ErrBadRequest,
		}
	}

	v, err := semver.NewVersion(bcr.Version)
	if err != nil {
		return &rerr.RegistryError{
			Message: fmt.Sprintf("invalid version: %s, %v", bcr.Version, err),
			Code:    rerr.ErrBadRequest,
		}
	}
	bcr.Version = v.String()

	if !slices.Contains(SupportedKind, bcr.Kind) {
		return &rerr.RegistryError{
			Message: fmt.Sprintf("unsupported kind: %s, allowed values are: %v", bcr.Kind, SupportedKind),
			Code:    rerr.ErrBadRequest,
		}
	}

	if !slices.Contains(SupportedType, bcr.Type) {
		return &rerr.RegistryError{
			Message: fmt.Sprintf("unsupported type: %s, allowed values are: %v", bcr.Type, SupportedType),
			Code:    rerr.ErrBadRequest,
		}
	}

	return bcr.Specification.Validate()
}
