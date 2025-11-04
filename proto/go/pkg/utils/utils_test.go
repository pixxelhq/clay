package utils

import (
	"errors"
	"fmt"
	"testing"
)

func Test_Function_GetField(t *testing.T) {
	type anotherStruct struct {
		A int
		B int
	}
	type testStruct struct {
		Name           string
		IntVal         int
		FloatVal       float32
		MapVal         map[string]interface{}
		StringSliceVal []string
		StructVal      *anotherStruct
		NilField       interface{}
	}

	foo := anotherStruct{A: 1, B: 2}
	bar := testStruct{
		Name:           "bar",
		IntVal:         100,
		FloatVal:       200.22,
		MapVal:         map[string]interface{}{"hello": "world"},
		StringSliceVal: []string{"X", "Y"},
		StructVal:      &foo,
		NilField:       nil,
	}

	v, err := GetField(&bar, "Name")
	if err != nil || v != "bar" {
		t.Error(fmt.Sprintf(
			"failed: expected: %+v, %+v, got: %+v, %+v", "name", nil, v, err),
		)
	}

	v, err = GetField(&bar, "IntVal")
	if err != nil || v != 100 {
		t.Error(fmt.Sprintf(
			"failed: expected: %+v, %+v, got: %+v, %+v", 100, nil, v, err,
		))
	}

	v, err = GetField(&bar, "StructVal")
	if err != nil || v != &foo {
		t.Error(fmt.Sprintf(
			"failed: expected: %+v, %+v, got: %+v, %+v", &foo, nil, v, err,
		))
	}

	v, err = GetField(&bar, "NilField")
	if err != nil || v != nil {
		t.Error(fmt.Sprintf(
			"failed: expected: %+v, %+v, got: %+v, %+v", nil, nil, v, err,
		))
	}

	v, err = GetField(&bar, "unknownField")
	if !errors.Is(err, ErrUnknownField) || v != nil {
		t.Error(fmt.Sprintf(
			"failed: expected: %+v, %+v, got: %+v, %+v", nil, ErrUnknownField, v, err,
		))
	}
}

func Test_Function_SetField(t *testing.T) {
	type anotherStruct struct {
		A int
		B int
	}
	type testStruct struct {
		Name           string
		IntVal         int
		FloatVal       float32
		MapVal         map[string]interface{}
		StringSliceVal []string
		StructVal      *anotherStruct
		NilField       interface{}
	}

	foo := anotherStruct{A: 1, B: 2}
	bar := testStruct{
		Name:           "bar",
		IntVal:         100,
		FloatVal:       200.22,
		MapVal:         map[string]interface{}{"hello": "world"},
		StringSliceVal: []string{"X", "Y"},
		StructVal:      &foo,
		NilField:       nil,
	}

	err := SetField(&bar, "Name", "new bar")
	if err != nil || bar.Name != "new bar" {
		t.Error(
			fmt.Sprintf(
				"failed: expected: %+v, %+v, got: %+v, %+v", nil, "new bar", err, bar.Name,
			),
		)
		t.FailNow()
	}
	err = SetField(&bar, "FloatVal", 10.4)
	if err != nil || bar.FloatVal != 10.4 {
		t.Error(
			fmt.Sprintf(
				"failed: expected: %+v, %+v, got: %+v, %+v", nil, 10.4, err, bar.FloatVal,
			),
		)
		t.FailNow()
	}
	err = SetField(&bar, "FloatVal", "please fail")
	if !errors.Is(err, ErrIncompatibleType) || bar.FloatVal != 10.4 {
		t.Error(
			fmt.Sprintf(
				"failed: expected: %+v, %+v, got: %+v, %+v", ErrIncompatibleType, 10.4, err, bar.FloatVal,
			),
		)
		t.FailNow()
	}
	err = SetField(&bar, "unknown field", "please fail")
	if !errors.Is(err, ErrUnknownField) {
		t.Error(
			fmt.Sprintf(
				"failed: expected: %+v, got: %+v", ErrUnknownField, err,
			),
		)
		t.FailNow()
	}
	err = SetField(&bar, "NilField", 120.0)
	if err != nil || bar.NilField != 120.0 {
		t.Error(
			fmt.Sprintf(
				"failed: expected: %+v, %+v, got: %+v, %+v", nil, 120.0, err, bar.NilField,
			),
		)
		t.FailNow()
	}
}
