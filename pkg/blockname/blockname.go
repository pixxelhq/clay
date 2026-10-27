// Package blockname derives the names a block uses in its project files
// from the single name the user gives to `clay new`.
package blockname

import (
	"fmt"
	"regexp"
	"strings"
)

// Names holds every form of a block name used by the scaffold.
type Names struct {
	Slug   string // kebab-case: clay.yaml name and image; also valid in Kubernetes names
	Module string // snake_case: Python package, as Python cannot import names with '-'
	Class  string // CamelCase: Python class
}

var validName = regexp.MustCompile(`^[A-Za-z]([A-Za-z0-9_-]*[A-Za-z0-9])?$`)

// Parse returns the forms of name: "my-block", "my_block" and "My-Block"
// give {my-block, my_block, MyBlock}, and "MyBlock" gives {myblock, myblock, MyBlock}.
func Parse(name string) (Names, error) {
	if !validName.MatchString(name) {
		return Names{}, fmt.Errorf(
			"invalid block name %q: start with a letter, end with a letter or digit, "+
				"and use only letters, digits, '-' and '_'", name)
	}

	var class strings.Builder
	for _, word := range strings.FieldsFunc(name, func(r rune) bool { return r == '-' || r == '_' }) {
		class.WriteString(strings.ToUpper(word[:1]) + word[1:])
	}
	return Names{
		Slug:   strings.ToLower(strings.ReplaceAll(name, "_", "-")),
		Module: strings.ToLower(strings.ReplaceAll(name, "-", "_")),
		Class:  class.String(),
	}, nil
}
