package store

import (
	"database/sql"

	"github.com/lib/pq"

	rerr "github.com/example/clay/registry/pkg/error"
)

func PGErrorToRegistryError(err error) *rerr.RegistryError {
	if err == sql.ErrNoRows {
		return &rerr.RegistryError{
			Code: rerr.ErrDoesNotExists,
			Err:  err,
		}
	}

	switch v := err.(type) {
	case *pq.Error:
		switch v.Code {
		case "23505":
			return &rerr.RegistryError{
				Code: rerr.ErrAlreadyExists,
				Err:  err,
			}
		case "02000":
			return &rerr.RegistryError{
				Code: rerr.ErrDoesNotExists,
				Err:  err,
			}
		}

	default:
		return &rerr.RegistryError{
			Code: rerr.ErrInternal,
			Err:  err,
		}
	}

	return &rerr.RegistryError{
		Code: rerr.ErrInternal,
		Err:  err,
	}
}
