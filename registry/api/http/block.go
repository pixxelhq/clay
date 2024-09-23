package http

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type blockHandler struct {
}

func NewBlock() *blockHandler {
	return &blockHandler{}
}

func (b *blockHandler) Create(ctx *gin.Context) {
	var req BlockCreateRequest
	if err := ctx.BindJSON(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, &RegistryResponse[any]{
			Error: err.Error(),
		})
		return
	}

	ctx.JSON(http.StatusCreated, &RegistryResponse[BlockCreateResponse]{})
}
