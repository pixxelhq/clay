package block

import (
	"fmt"

	"github.com/example/clay/pkg"
)

type Status int

const (
	Draft Status = iota
	Released
	Disabled
)

func (s Status) String() string {
	return [...]string{"draft", "released", "disabled"}[s]
}
func ParseStatusOptions(st string) (s Status, err error) {
	var status Status
	switch st {
	case "draft":
		status = Draft
	case "released":
		status = Released
	case "disabled":
		status = Disabled
	default:
		return status, pkg.ErrInvalidValue(fmt.Sprintf("Invalid status value: %s", s))
	}
	return status, nil
}

type Env int

const (
	Dev Env = iota
	Stg
	Prod
)

func (e Env) String() string {
	return [...]string{"dev", "stg", "prod"}[e]
}

func ParseEnvOptions(ev string) (e Env, err error) {
	var env Env
	switch ev {
	case "dev":
		env = Dev
	case "stg":
		env = Stg
	case "prod":
		env = Prod
	default:
		return env, pkg.ErrInvalidValue(fmt.Sprintf("Invalid env value: %s", ev))
	}
	return env, nil
}
