package http

import (
	"time"

	"github.com/pixxelhq/clay-framework/registry/pkg/log"

	"github.com/gin-gonic/gin"
)

func Logger() gin.HandlerFunc {
	return func(ctx *gin.Context) {
		start := time.Now()
		log.Infof("started method: [%s], url: %s", ctx.Request.Method, ctx.Request.URL)

		ctx.Next()

		end := time.Now()

		latency := end.Sub(start)
		log.Infof("ended method: [%s], url: %s, time: %s", ctx.Request.Method, ctx.Request.URL, latency)
	}
}
