package store

import (
	rerr "registry/pkg/error"

	"github.com/lib/pq"
)

func PGErrorToRegistryError(err error) *rerr.RegistryError {
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
