package errors

import (
	"fmt"
)

// RegistryError represents an error that could be wrapping another error, it includes a code for determining what
// triggered the error.
type RegistryError struct {
	Message string
	Err     error
	Code    ErrorCode
}

const (
	ErrDoesNotExists ErrorCode = "DOES NOT EXISTS"
	ErrInternal      ErrorCode = "INTERNAL ERROR"
	ErrBadRequest    ErrorCode = "BAD REQUEST"
	ErrAlreadyExists ErrorCode = "ALREADY EXISTS"
)

var PGCodeToRegistryCode = map[string]ErrorCode{
	"23505": ErrAlreadyExists,
}

type ErrorCode string

func (de *RegistryError) Error() string {
	if de.Err != nil {
		return fmt.Sprintf("code: %v, err: %v, %v", de.Code, de.Message, de.Err)
	}
	return fmt.Sprintf("code: %v, err: %v", de.Code, de.Message)
}

func WrapError(original error, code ErrorCode, msg string) error {
	return &RegistryError{
		Code:    code,
		Err:     original,
		Message: msg,
	}
}

func (de *RegistryError) Unwrap() error {
	return de.Err
}

// NewError instantiates a new error.
func NewError(code ErrorCode, msg string) error {
	return WrapError(nil, code, msg)
}
