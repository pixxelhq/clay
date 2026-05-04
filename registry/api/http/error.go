package http

import (
	"errors"
	"net/http"

	rerr "github.com/pixxelhq/clay-framework/registry/pkg/error"
	"github.com/pixxelhq/clay-framework/registry/pkg/log"

	"github.com/gin-gonic/gin"
)

func handleErr(ctx *gin.Context, err error) {
	log.Errorf("error for %s:, %v", ctx.FullPath(), err)

	var re *rerr.RegistryError
	if errors.As(err, &re) {
		switch re.Code {
		case rerr.ErrBadRequest:
			ctx.JSON(http.StatusBadRequest, RegistryResponse[any]{
				Error: re.Message,
			})
			return
		case rerr.ErrDoesNotExists:
			ctx.JSON(http.StatusNotFound, RegistryResponse[any]{
				Error: re.Message,
			})
			return
		case rerr.ErrAlreadyExists:
			ctx.JSON(http.StatusConflict, RegistryResponse[any]{
				Error: re.Message,
			})
			return
		default:
			ctx.JSON(http.StatusInternalServerError, RegistryResponse[any]{
				Error: "something went wrong",
			})
			return
		}
	}

	ctx.JSON(http.StatusInternalServerError, RegistryResponse[any]{
		Error: "something went wrong",
	})
}
