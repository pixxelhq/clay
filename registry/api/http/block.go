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

func (bh *blockHandler) Create(ctx *gin.Context) {
	var req CreateBlockRequest
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

	blk, err := bh.service.Create(ctx, convertToServiceBlock(req))
	if err != nil {
		handleErr(ctx, err)
		return
	}

	ctx.JSON(http.StatusCreated, &RegistryResponse[CreateBlockResponse]{
		Data: CreateBlockResponse{
			ID:            blk.ID,
			Name:          blk.Name,
			Type:          blk.Type,
			Version:       blk.Version,
			CreatedAt:     blk.CreatedAt,
			UpdatedAt:     blk.UpdatedAt,
			Specification: convertFromServiceSpecification(blk.Specification),
		},
	})
}

func (bh *blockHandler) GetBlocksWithLatestVersion(ctx *gin.Context) {
	bwlv, err := bh.service.GetBlocksWithLatestVersion(ctx)
	if err != nil {
		handleErr(ctx, err)
		return
	}

	blocks := make([]*GetLatestBlock, 0, len(bwlv))
	for _, b := range bwlv {
		blocks = append(blocks, &GetLatestBlock{
			ID:            b.ID,
			Name:          b.Name,
			Version:       b.Version,
			Specification: convertFromServiceSpecification(b.Specification),
			CreatedAt:     b.CreatedAt,
			UpdatedAt:     b.UpdatedAt,
			Type:          b.Type,
		})
	}

	ctx.JSON(http.StatusOK, &RegistryResponse[[]*GetLatestBlock]{
		Data: blocks,
	})
}

func (bh *blockHandler) GetBlockByName(ctx *gin.Context) {
	name := ctx.Param("name")
	if name == "" {
		ctx.JSON(http.StatusBadRequest, &RegistryResponse[any]{
			Error: "name can't be empty",
		})
		return
	}

	blockVersions, err := bh.service.GetBlockByName(ctx, name)
	if err != nil {
		handleErr(ctx, err)
		return
	}

	blocks := make([]*GetBlockVersion, 0, len(blockVersions))
	for _, b := range blockVersions {
		blocks = append(blocks, &GetBlockVersion{
			ID:            b.ID,
			Name:          b.Name,
			Version:       b.Version,
			Specification: convertFromServiceSpecification(b.Specification),
			CreatedAt:     b.CreatedAt,
			UpdatedAt:     b.UpdatedAt,
			Type:          b.Type,
		})
	}

	ctx.JSON(http.StatusOK, &RegistryResponse[[]*GetBlockVersion]{
		Data: blocks,
	})

}

func (bh *blockHandler) GetBlockByNameAndVersion(ctx *gin.Context) {
	name := ctx.Param("name")
	if name == "" {
		ctx.JSON(http.StatusBadRequest, &RegistryResponse[any]{
			Error: "name can't be empty",
		})
		return
	}

	version := ctx.Param("version")
	if version == "" {
		ctx.JSON(http.StatusBadRequest, &RegistryResponse[any]{
			Error: "name can't be empty",
		})
		return
	}

	b, err := bh.service.GetBlockByNameAndVersion(ctx, name, version)
	if err != nil {
		handleErr(ctx, err)
		return
	}

	ctx.JSON(http.StatusOK, &RegistryResponse[*GetBlockVersion]{
		Data: &GetBlockVersion{
			ID:            b.ID,
			Name:          b.Name,
			Kind:          b.Kind,
			Type:          b.Type,
			Version:       b.Version,
			Specification: convertFromServiceSpecification(b.Specification),
			CreatedAt:     b.CreatedAt,
			UpdatedAt:     b.UpdatedAt,
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

func convertToServiceBlock(req CreateBlockRequest) *block.Block {
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
