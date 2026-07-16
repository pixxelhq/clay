package store

import (
	"context"
	"database/sql"

	"github.com/pixxelhq/clay/registry/pkg/log"
)

type Store interface {
	ExecWithTx(ctx context.Context, fn func(q Querier) (any, error)) (any, error)
	Querier
}

type SQLStore struct {
	db *sql.DB
	*Queries
}

func NewStore(db *sql.DB) *SQLStore {
	return &SQLStore{
		db:      db,
		Queries: New(db),
	}
}

func (s *SQLStore) ExecWithTx(ctx context.Context, fn func(q Querier) (any, error)) (any, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}

	q := New(tx)
	data, err := fn(q)
	if err != nil {
		if rbErr := tx.Rollback(); rbErr != nil {
			log.Errorf("error while executing the tx rollback, err: %v, rollback err: %v", err, rbErr)
		}
		return nil, err
	}

	return data, tx.Commit()
}
