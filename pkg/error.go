package pkg

type InvalidValueError struct {
	Msg string
}

func (i InvalidValueError) Error() string {
	return i.Msg
}

func ErrInvalidValue(msg string) error {
	return InvalidValueError{Msg: msg}
}
