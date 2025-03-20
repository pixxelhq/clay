package http

import (
	"net/http"

	"github.com/example/clay/registry/pkg/block"

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

// Publish Block	godoc
//
//	@Summary		Publish the model to clay registry
//	@Description	publish the specific version of the model.
//	@Tags			Block
//
//	@Produce		json
//	@Success		200	{object}	RegistryResponse[CreateBlockResponse]
//	@Failure		400	{object}	RegistryResponse[any]
//	@Failure		500	{object}	RegistryResponse[any]
//	@Router			/v1/blocks [post]
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

// GetBlocksWithLatestVersion	godoc
//
//	@Summary		Get the latest models from the registry
//	@Description	Return all the model with latest version.
//	@Tags			Block
//
//	@Produce		json
//	@Success		200	{object}	RegistryResponse[GetLatestBlocksResponse]
//	@Failure		400	{object}	RegistryResponse[any]
//	@Failure		500	{object}	RegistryResponse[any]
//	@Router			/v1/blocks [get]
func (bh *blockHandler) GetBlocksWithLatestVersion(ctx *gin.Context) {
	bwlv, err := bh.service.GetBlocksWithLatestVersion(ctx)
	if err != nil {
		handleErr(ctx, err)
		return
	}

	blocks := make([]*GetLatestBlock, 0, len(bwlv))
	for _, b := range bwlv {
		blocks = append(blocks, &GetLatestBlock{
			ID:               b.ID,
			Name:             b.Name,
			Type:             b.Type,
			Kind:             b.Kind,
			Version:          b.Version,
			CreatedAt:        b.CreatedAt,
			DockerImage:      b.DockerImage,
			DocumentationURL: b.DocumentationURL,
			UpdatedAt:        b.UpdatedAt,
		})
	}

	ctx.JSON(http.StatusOK, &RegistryResponse[GetLatestBlocksResponse]{
		Data: blocks,
	})
}

// GetBlockByName	godoc
//
//	@Summary		Get model by name.
//	@Description	Returns all the versions of the model name.
//	@Tags			Block
//
//	@Produce		json
//	@Param			name		path	string		true	"Name of the model"
//	@Success		200	{object}	RegistryResponse[GetBlocksByNameResponse]
//	@Failure		400	{object}	RegistryResponse[any]
//	@Failure		500	{object}	RegistryResponse[any]
//	@Router			/v1/blocks/{name} [get]
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

	blocks := make([]*GetBlockByNameAndVersion, 0, len(blockVersions))
	for _, b := range blockVersions {
		blocks = append(blocks, &GetBlockByNameAndVersion{
			ID:               b.ID,
			Name:             b.Name,
			Type:             b.Type,
			Kind:             b.Kind,
			Version:          b.Version,
			DockerImage:      b.DockerImage,
			DocumentationURL: b.DocumentationURL,
			Specification:    convertFromServiceSpecification(b.Specification),
			CreatedAt:        b.CreatedAt,
			UpdatedAt:        b.UpdatedAt,
		})
	}

	ctx.JSON(http.StatusOK, &RegistryResponse[GetBlocksByNameResponse]{
		Data: blocks,
	})
}

// GetBlockByNameAndVersion	godoc
//
//	@Summary		Get model by name and version.
//	@Description	Returns the model for the given version and name.
//	@Tags			Block
//
//	@Param			name		path	string		true	"Name of the model"
//	@Param			version		path	string		true	"Version of the model"
//	@Produce		json
//	@Success		200	{object}	RegistryResponse[GetBlockByNameAndVersion]
//	@Failure		400	{object}	RegistryResponse[any]
//	@Failure		500	{object}	RegistryResponse[any]
//	@Router			/v1/blocks/{name}/versions/{version} [get]
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
			Error: "version can't be empty",
		})
		return
	}

	b, err := bh.service.GetBlockByNameAndVersion(ctx, name, version)
	if err != nil {
		handleErr(ctx, err)
		return
	}

	ctx.JSON(http.StatusOK, &RegistryResponse[*GetBlockByNameAndVersion]{
		Data: &GetBlockByNameAndVersion{
			ID:               b.ID,
			Name:             b.Name,
			Kind:             b.Kind,
			Type:             b.Type,
			Version:          b.Version,
			DockerImage:      b.DockerImage,
			DocumentationURL: b.DocumentationURL,
			Specification:    convertFromServiceSpecification(b.Specification),
			CreatedAt:        b.CreatedAt,
			UpdatedAt:        b.UpdatedAt,
		},
	})
}

func convertFromServiceSpecification(bSpec *block.Specification) *Specification {
	return &Specification{
		APIVersion: bSpec.Version,
		Author:     bSpec.Author,
		Tags:       bSpec.Tags,
		Parameters: bSpec.Parameters,
		Inputs:     bSpec.Inputs,
		Outputs:    bSpec.Outputs,
		Build:      bSpec.Build,
		ENV:        bSpec.ENV,
		GPU:        bSpec.GPU,
	}
}

func convertToServiceSpecification(s *Specification) *block.Specification {
	return &block.Specification{
		Version:    s.APIVersion,
		Author:     s.Author,
		Tags:       s.Tags,
		Parameters: s.Parameters,
		Inputs:     s.Inputs,
		Outputs:    s.Outputs,
		Build:      s.Build,
		ENV:        s.ENV,
		GPU:        s.GPU,
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
