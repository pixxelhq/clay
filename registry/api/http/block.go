package http

import (
	"net/http"
	"registry/pkg/block"

	"github.com/gin-gonic/gin"
)

type blockHandler struct {
	service block.Service
}

func NewBlock(s block.Service) *blockHandler {
	return &blockHandler{
		service: s,
	}
}

func (b *blockHandler) Create(ctx *gin.Context) {
	var req BlockCreateRequest
	if err := ctx.BindJSON(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, &RegistryResponse[any]{
			Error: err.Error(),
		})
		return
	}

	if err := req.Validate(); err != nil {
		ctx.JSON(http.StatusBadRequest, &RegistryResponse[any]{
			Error: err.Error(),
		})
		return
	}

	blk, err := b.service.Create(ctx, convertToServiceBlock(req))
	if err != nil {
		handleErr(ctx, err)
		return
	}

	ctx.JSON(http.StatusCreated, &RegistryResponse[BlockCreateResponse]{
		Data: BlockCreateResponse{
			ID:            blk.ID,
			Name:          blk.Name,
			Type:          blk.Type,
			CreatedAt:     blk.CreatedAt,
			UpdatedAt:     blk.UpdatedAt,
			Specification: convertFromServiceSpecification(blk.Specification),
		},
	})
}

func convertFromServiceSpecification(bSpec *block.Specification) *Specification {
	return &Specification{
		Version:     bSpec.Version,
		Title:       bSpec.Title,
		Description: bSpec.Description,
		Author:      bSpec.Author,
		Tags:        bSpec.Tags,
		Parameters:  bSpec.Parameters,
		Inputs:      bSpec.Inputs,
		Outputs:     bSpec.Outputs,
		Build:       bSpec.Build,
	}
}

func convertToServiceSpecification(s *Specification) *block.Specification {
	return &block.Specification{
		Version:     s.Version,
		Title:       s.Title,
		Description: s.Description,
		Author:      s.Author,
		Tags:        s.Tags,
		Parameters:  s.Parameters,
		Inputs:      s.Inputs,
		Outputs:     s.Outputs,
		Build:       s.Build,
	}
}

func convertToServiceBlock(req BlockCreateRequest) *block.Block {
	return &block.Block{
		Name:             req.Name,
		Kind:             req.Kind,
		Type:             req.Type,
		Version:          req.Version,
		DocumentationURL: req.DocumentationURL,
		DockerImage:      req.DockerImage,
		Specification:    convertToServiceSpecification(req.Specification),
	}
}
