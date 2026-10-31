package http

import (
	"database/sql"
	"errors"
	"fmt"
	llog "log"
	"net"
	"net/http"

	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/pixxelhq/clay/registry/config"
	store "github.com/pixxelhq/clay/registry/internal/store/sqlc"
	"github.com/pixxelhq/clay/registry/pkg/block"
	"github.com/pixxelhq/clay/registry/pkg/log"

	"github.com/gin-gonic/gin"
	"github.com/golang-migrate/migrate/v4"
	_ "github.com/golang-migrate/migrate/v4/database/postgres"
	"github.com/golang-migrate/migrate/v4/source"
	_ "github.com/golang-migrate/migrate/v4/source/file"
	"github.com/lib/pq"
	swaggerfiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

type Server struct {
	Router *gin.Engine
	Cfg    *config.Config
	Store  store.Store

	Block block.Service
}

func NewServer() *Server {
	return &Server{
		Router: gin.Default(),
	}
}

func (svr *Server) Init() {
	// don't change the order of the functions
	requireFn(
		svr.LoadConfig,
		svr.InitLogger,
		svr.RunMigration,
		svr.ConfigureStore,
		svr.ConfigureService,
		svr.MapRoutes,
		svr.ConfigureSwagger,
		svr.ConfigureMetric,
	)
}

func (svr *Server) LoadConfig() error {
	err := config.Load()
	if err != nil {
		return err
	}

	svr.Cfg = &config.App
	return nil
}

func (svr *Server) InitLogger() error {
	return log.InitLogger(svr.Cfg.LogLevel)
}

func (svr *Server) dsn() string {
	return fmt.Sprintf("postgres://%s:%s@%s:%d/%s?sslmode=disable", svr.Cfg.DBUserName, svr.Cfg.DBPassword, svr.Cfg.DBHost, svr.Cfg.DBPort, svr.Cfg.DBName)
}

func (svr *Server) dbConnError(err error) error {
	var (
		opErr *net.OpError
		pqErr *pq.Error
	)
	reason := "unknown error"
	switch {
	case errors.As(err, &pqErr):
		reason = pqErr.Code.Name()
	case errors.As(err, &opErr):
		reason = opErr.Err.Error()
	}
	return fmt.Errorf("cannot connect to database %q on host %q: %s", svr.Cfg.DBName, svr.Cfg.DBHost, reason)
}

func (svr *Server) ConfigureStore() error {
	conn, err := sql.Open("postgres", svr.dsn())
	if err != nil {
		return svr.dbConnError(err)
	}

	err = conn.Ping()
	if err != nil {
		return svr.dbConnError(err)
	}

	svr.Store = store.NewStore(conn)
	return nil
}

func (svr *Server) RunMigration() error {
	src, err := source.Open(svr.Cfg.DBMigrationPath)
	if err != nil {
		return fmt.Errorf("failed to load migrations from %s: %w", svr.Cfg.DBMigrationPath, err)
	}

	m, err := migrate.NewWithSourceInstance("file", src, svr.dsn())
	if err != nil {
		return svr.dbConnError(err)
	}

	if err := m.Up(); err != nil && err != migrate.ErrNoChange {
		log.Errorf("error running migration: %v\n", err)
		log.Info("rolling back migration due to above failure")
		if rbErr := m.Steps(-1); rbErr != nil {
			log.Errorf("error rolling back migration: %v\n", rbErr)
			return rbErr
		}
	}

	return nil
}

func (svr *Server) ConfigureService() error {
	if svr.Store == nil {
		return fmt.Errorf("store must be configured before the services")
	}

	blockService := block.New(svr.Store)
	svr.Block = blockService

	return nil
}

func (svr *Server) ConfigureSwagger() error {
	svr.Router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerfiles.Handler))
	return nil
}

func (svr *Server) ConfigureMetric() error {
	svr.Router.GET("/metrics", func(ctx *gin.Context) {
		h := promhttp.Handler()
		h.ServeHTTP(ctx.Writer, ctx.Request)
	})
	return nil
}

func requireFn(fns ...func() error) {
	for _, fn := range fns {
		if err := fn(); err != nil {
			llog.Fatalf("error: %v\n", err)
		}
	}
}

func (svr *Server) Start() error {
	svr.Router.GET("/ping", func(ctx *gin.Context) {
		ctx.JSON(http.StatusOK, `{pong}`)
	})

	return svr.Router.Run(fmt.Sprintf(":%d", svr.Cfg.HTTPPort))
}
