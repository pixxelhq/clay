package block

import (
	"context"
	"database/sql"
	"encoding/json"
	store "registry/internal/store/sqlc"
	rerr "registry/pkg/error"
	"registry/pkg/log"
	"time"
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
			DocumenatationUrl: sql.NullString{
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
			Name:             upsertedBlock.Name,
			Kind:             upsertedBlock.Kind,
			Type:             upsertedBlock.Type,
			DocumentationURL: bv.DocumenatationUrl.String,
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
