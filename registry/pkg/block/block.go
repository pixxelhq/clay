package block

import (
	"context"
	"database/sql"
	"encoding/json"
	"time"

	"github.com/Masterminds/semver"
	store "github.com/pixxelhq/clay-framework/registry/internal/store/sqlc"
	rerr "github.com/pixxelhq/clay-framework/registry/pkg/error"
	"github.com/pixxelhq/clay-framework/registry/pkg/log"
)

type Specification struct {
	Version     string          `json:"apiVersion"`
	Title       string          `json:"title"`
	Description string          `json:"description"`
	Author      string          `json:"author"`
	Tags        []string        `json:"tags"`
	Parameters  json.RawMessage `json:"parameters"`
	Inputs      json.RawMessage `json:"inputs"`
	Outputs     json.RawMessage `json:"outputs"`
	Build       json.RawMessage `json:"build"`
	ENV         json.RawMessage `json:"env"`
	GPU         bool            `json:"gpu"`
}

type Block struct {
	ID               string
	Name             string
	Kind             string
	Type             string
	Version          string
	Specification    *Specification
	CatalogURL       string
	DocumentationURL string
	ThumbnailURL     string
	DockerImage      string
	CreatedAt        time.Time
	UpdatedAt        time.Time
}

type Service interface {
	Create(ctx context.Context, block *Block) (*Block, error)
	GetBlocksWithLatestVersion(ctx context.Context) ([]*Block, error)
	GetBlockByName(ctx context.Context, name string) ([]*Block, error)
	GetBlockByNameAndVersion(ctx context.Context, name, version string) (*Block, error)
}

type block struct {
	store store.Store
}

func New(s store.Store) Service {
	return &block{
		store: s,
	}
}

func (bs *block) Create(ctx context.Context, b *Block) (*Block, error) {
	resp, err := bs.store.ExecWithTx(ctx, func(q store.Querier) (any, error) {
		upsertedBlock, err := q.UpsertBlock(ctx, store.UpsertBlockParams{
			Name: b.Name,
			Kind: b.Kind,
			Type: b.Type,
		})
		if err != nil {
			log.Errorf("error while upserting block with name %s, %v", b.Name, err)
			return nil, err
		}

		specByte, err := json.Marshal(b.Specification)
		if err != nil {
			log.Errorf("error while marshaling specification: %v", err)
			return nil, err
		}

		bv, err := q.CreateBlockVersion(ctx, store.CreateBlockVersionParams{
			BlockID:       upsertedBlock.ID,
			Version:       b.Version,
			Specification: specByte,
			DocumentationUrl: sql.NullString{
				String: b.DocumentationURL,
				Valid:  b.DocumentationURL != "",
			},
			ThumbnailUrl: sql.NullString{
				String: b.ThumbnailURL,
				Valid:  b.ThumbnailURL != "",
			},
			CatalogUrl: sql.NullString{
				String: b.CatalogURL,
				Valid:  b.CatalogURL != "",
			},
			DockerImage: sql.NullString{
				String: b.DockerImage,
				Valid:  true,
			},
		})
		if err != nil {
			errV := store.PGErrorToRegistryError(err)
			if errV.Code == rerr.ErrAlreadyExists {
				errV.Message = "block with the given name and version already exists"
			}
			return nil, errV
		}

		spec := &Specification{}
		err = json.Unmarshal(bv.Specification, spec)
		if err != nil {
			return nil, err
		}
		return &Block{
			ID:               upsertedBlock.ID.String(),
			Version:          bv.Version,
			Name:             upsertedBlock.Name,
			Kind:             upsertedBlock.Kind,
			Type:             upsertedBlock.Type,
			DocumentationURL: bv.DocumentationUrl.String,
			ThumbnailURL:     bv.ThumbnailUrl.String,
			CatalogURL:       bv.CatalogUrl.String,
			DockerImage:      bv.DockerImage.String,
			Specification:    spec,
			CreatedAt:        bv.CreatedAt.Time,
			UpdatedAt:        bv.UpdatedAt.Time,
		}, nil
	})
	if err != nil {
		return nil, err
	}

	return resp.(*Block), nil
}

func (bs *block) GetBlocksWithLatestVersion(ctx context.Context) ([]*Block, error) {
	blocks, err := bs.store.GetAllBlocks(ctx)
	if err != nil {
		return nil, err
	}
	if len(blocks) == 0 {
		return []*Block{}, nil
	}

	/*
		This is inefficient, as it is making db call for each block.

		Reason: Versions can include value like 1.2.3, 1.2.3-alpha, 1.2.3-alpha.1,
		and versions sorting is not included in the query, becuase there is
		no staright forward way to do the sorting of string versions correctly in sql.
	*/

	latestBlocks := make([]*Block, 0, len(blocks))
	for _, block := range blocks {
		blockVersion, err := bs.GetLatestBlock(ctx, block.Name)
		if err != nil {
			return nil, err
		}
		if blockVersion != nil {
			latestBlocks = append(latestBlocks, blockVersion)
		}
	}

	return latestBlocks, nil
}

func (bs *block) GetBlockByName(ctx context.Context, name string) ([]*Block, error) {
	blockVersions, err := bs.store.GetBlockAllVersionByName(ctx, name)
	if store.PGErrorToRegistryError(err).Code == rerr.ErrDoesNotExists {
		return []*Block{}, nil
	}
	if err != nil {
		return nil, err
	}

	blocks := make([]*Block, 0, len(blockVersions))
	for _, b := range blockVersions {
		spec := &Specification{}
		err = json.Unmarshal(b.Specification, spec)
		if err != nil {
			return nil, err
		}
		blocks = append(blocks, &Block{
			ID:               b.ID.String(),
			Name:             b.Name,
			Type:             b.Type,
			Kind:             b.Kind,
			Version:          b.Version,
			Specification:    spec,
			DocumentationURL: b.DocumentationUrl.String,
			ThumbnailURL:     b.ThumbnailUrl.String,
			DockerImage:      b.DockerImage.String,
			CreatedAt:        b.CreatedAt.Time,
			UpdatedAt:        b.UpdatedAt.Time,
		})
	}

	return blocks, nil
}

func (bs *block) GetBlockByNameAndVersion(ctx context.Context, name, version string) (*Block, error) {
	if version == "latest" {
		return bs.GetLatestBlock(ctx, name)
	}

	blockWithNameAndVersion, err := bs.store.GetBlockByNameAndVersion(ctx, store.GetBlockByNameAndVersionParams{
		Name:    name,
		Version: version,
	})
	if err != nil {
		pgErr := store.PGErrorToRegistryError(err)
		if pgErr.Code == rerr.ErrDoesNotExists {
			pgErr.Message = "block with the given name and version does not exists"
		}
		return nil, pgErr
	}
	spec := &Specification{}
	err = json.Unmarshal(blockWithNameAndVersion.Specification, spec)
	if err != nil {
		return nil, err
	}
	return &Block{
		ID:               blockWithNameAndVersion.ID.String(),
		Name:             blockWithNameAndVersion.Name,
		Version:          blockWithNameAndVersion.Version,
		DockerImage:      blockWithNameAndVersion.DockerImage.String,
		DocumentationURL: blockWithNameAndVersion.DocumentationUrl.String,
		ThumbnailURL:     blockWithNameAndVersion.ThumbnailUrl.String,
		Specification:    spec,
		CatalogURL:       blockWithNameAndVersion.CatalogUrl.String,
		Kind:             blockWithNameAndVersion.Kind,
		Type:             blockWithNameAndVersion.Type,
		CreatedAt:        blockWithNameAndVersion.CreatedAt.Time,
		UpdatedAt:        blockWithNameAndVersion.UpdatedAt.Time,
	}, nil
}

func (bs *block) GetLatestBlock(ctx context.Context, name string) (*Block, error) {
	blockVersions, err := bs.store.GetBlockAllVersionByName(ctx, name)
	if store.PGErrorToRegistryError(err).Code == rerr.ErrDoesNotExists {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if len(blockVersions) == 0 {
		return nil, rerr.NewError(rerr.ErrDoesNotExists, "block with the given name does not exist")
	}

	var (
		latestBlock   store.GetBlockAllVersionByNameRow
		latestVersion *semver.Version
	)

	for i, block := range blockVersions {
		v, err := semver.NewVersion(block.Version)
		if err != nil {
			log.Warnf("invalid semver format for block %s version %s: %v", name, block.Version, err)
			continue
		}

		if i == 0 || latestVersion.Compare(v) < 0 {
			latestVersion = v
			latestBlock = block
		}
	}

	if latestVersion == nil {
		return nil, rerr.NewError(rerr.ErrBadRequest, "no valid semver versions found for block")
	}

	spec := &Specification{}
	err = json.Unmarshal(latestBlock.Specification, spec)
	if err != nil {
		return nil, err
	}

	return &Block{
		ID:               latestBlock.ID.String(),
		Name:             latestBlock.Name,
		Version:          latestBlock.Version,
		DockerImage:      latestBlock.DockerImage.String,
		DocumentationURL: latestBlock.DocumentationUrl.String,
		ThumbnailURL:     latestBlock.ThumbnailUrl.String,
		Specification:    spec,
		Kind:             latestBlock.Kind,
		Type:             latestBlock.Type,
		CreatedAt:        latestBlock.CreatedAt.Time,
		UpdatedAt:        latestBlock.UpdatedAt.Time,
	}, nil
}
