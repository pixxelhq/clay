package block

import (
	"context"
	"database/sql"
	"encoding/json"
	"time"

	store "github.com/example/clay/registry/internal/store/sqlc"
	rerr "github.com/example/clay/registry/pkg/error"
	"github.com/example/clay/registry/pkg/log"
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
	DocumentationURL string
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
				Valid:  true,
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
	bwlv, err := bs.store.GetBlocksWithLatestVersion(ctx)
	if store.PGErrorToRegistryError(err).Code == rerr.ErrDoesNotExists {
		return []*Block{}, nil
	}
	if err != nil {
		return nil, err
	}

	blocks := make([]*Block, 0, len(bwlv))
	for _, b := range bwlv {
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
			DockerImage:      b.DockerImage.String,
			CreatedAt:        b.CreatedAt.Time,
			UpdatedAt:        b.UpdatedAt.Time,
		})
	}

	return blocks, nil
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
		Specification:    spec,
		Kind:             blockWithNameAndVersion.Kind,
		Type:             blockWithNameAndVersion.Type,
		CreatedAt:        blockWithNameAndVersion.CreatedAt.Time,
		UpdatedAt:        blockWithNameAndVersion.UpdatedAt.Time,
	}, nil
}

func (bs *block) GetLatestBlock(ctx context.Context, name string) (*Block, error) {
	b, err := bs.store.GetLatestBlockByName(ctx, name)
	if err != nil {
		pgErr := store.PGErrorToRegistryError(err)
		if pgErr.Code == rerr.ErrDoesNotExists {
			pgErr.Message = "block with the given name does not exists"
		}
		return nil, pgErr
	}

	spec := &Specification{}
	err = json.Unmarshal(b.Specification, spec)
	if err != nil {
		return nil, err
	}
	return &Block{
		ID:               b.ID.String(),
		Name:             b.Name,
		Version:          b.Version,
		DockerImage:      b.DockerImage.String,
		DocumentationURL: b.DocumentationUrl.String,
		Specification:    spec,
		Kind:             b.Kind,
		Type:             b.Type,
		CreatedAt:        b.CreatedAt.Time,
		UpdatedAt:        b.UpdatedAt.Time,
	}, nil
}
