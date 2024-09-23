package store

import "database/sql"

type Store interface {
	Querier
}

type SQLStore struct {
	// db *sql.DB
	*Queries
}

func NewStore(db *sql.DB) *SQLStore {
	return &SQLStore{
		Queries: New(db),
	}
}
