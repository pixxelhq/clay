package utils

import (
	"errors"
	"reflect"
)

var (
	ErrNotAPointer      = errors.New("value is not a pointer")
	ErrUnknownField     = errors.New("unknown field")
	ErrUnsettableField  = errors.New("unsettable field")
	ErrIncompatibleType = errors.New("incompatible type")
)

func GetField(t any, field string) (interface{}, error) {
	valueOf := reflect.ValueOf(t)
	if valueOf.Kind() != reflect.Ptr {
		return nil, ErrNotAPointer
	}
	fieldValue := reflect.Indirect(valueOf).FieldByName(field)
	if !fieldValue.IsValid() {
		return nil, ErrUnknownField
	}
	return fieldValue.Interface(), nil
}

func SetField(t any, field string, value interface{}) error {
	valueOf := reflect.ValueOf(t)
	if valueOf.Kind() != reflect.Ptr {
		return ErrNotAPointer
	}
	f := reflect.Indirect(valueOf).FieldByName(field)
	if !f.IsValid() {
		return ErrUnknownField
	}
	if !f.CanSet() {
		return ErrUnsettableField
	}
	v := reflect.ValueOf(value)
	if v.Type().ConvertibleTo(f.Type()) {
		f.Set(v.Convert(f.Type()))
	} else {
		return ErrIncompatibleType
	}
	return nil
}
