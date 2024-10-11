package http

import (
	"fmt"
	rerr "registry/pkg/error"
	"slices"
)

var (
	SupportedKind = []string{"block"}
	SupportedType = []string{"processing", "source"}
)

func (s *Specification) Validate() error {
	if s.Version == "" || s.Title == "" || s.Description == "" || s.Author == "" {
		return &rerr.RegistryError{
			Message: "specification: apiVersion, title, description and author can't be empty",
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

func (bcr *BlockCreateRequest) Validate() error {
	if bcr.Name == "" || bcr.Version == "" || bcr.DocumentationURL == "" || bcr.DockerImage == "" {
		return &rerr.RegistryError{
			Message: "name, version, docker_image and documentation_url can be empty",
			Code:    rerr.ErrBadRequest,
		}
	}

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
