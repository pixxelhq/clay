package config

import (
	"bytes"
	_ "embed"
	"errors"
	"fmt"
	"slices"
	"strings"

	"github.com/santhosh-tekuri/jsonschema/v6"
	"github.com/santhosh-tekuri/jsonschema/v6/kind"
	"golang.org/x/text/language"
	"golang.org/x/text/message"
)

const apiVersionV1 = "clay/v1"

const schemaV1URL = "https://pixxelhq.github.io/clay/schema/v1.json"

//go:embed schema/v1.json
var schemaV1JSON []byte

var schemaV1 = mustCompileSchemaV1()

var patternRules = map[string]string{
	"name":    "must start with a lowercase letter, end with a lowercase letter or digit, and use only lowercase letters, digits, '-' and '_'",
	"version": "must be a semantic version without a leading v, such as 1.2.3",
}

func mustCompileSchemaV1() *jsonschema.Schema {
	doc, err := jsonschema.UnmarshalJSON(bytes.NewReader(schemaV1JSON))
	if err != nil {
		panic(err)
	}
	compiler := jsonschema.NewCompiler()
	if err := compiler.AddResource(schemaV1URL, doc); err != nil {
		panic(err)
	}
	return compiler.MustCompile(schemaV1URL)
}

func validateV1(doc any) error {
	err := schemaV1.Validate(doc)
	var validationErr *jsonschema.ValidationError
	if !errors.As(err, &validationErr) {
		return err
	}

	printer := message.NewPrinter(language.English)
	var problems []string
	for _, leaf := range leafErrors(validationErr) {
		problems = append(problems, fmt.Sprintf("%s: %s", subjectAt(leaf.InstanceLocation), describe(leaf, printer)))
	}
	slices.Sort(problems)
	return fmt.Errorf("%s does not match the %s schema:\n  %s\nhint: see the clay.yaml reference: https://pixxelhq.github.io/clay/spec/",
		configFileName, apiVersionV1, strings.Join(problems, "\n  "))
}

func describe(err *jsonschema.ValidationError, printer *message.Printer) string {
	if _, ok := err.ErrorKind.(*kind.Pattern); ok && len(err.InstanceLocation) == 1 {
		if rule, ok := patternRules[err.InstanceLocation[0]]; ok {
			return rule
		}
	}
	return err.ErrorKind.LocalizedString(printer)
}

func leafErrors(err *jsonschema.ValidationError) []*jsonschema.ValidationError {
	if len(err.Causes) == 0 {
		return []*jsonschema.ValidationError{err}
	}
	var leaves []*jsonschema.ValidationError
	for _, cause := range err.Causes {
		leaves = append(leaves, leafErrors(cause)...)
	}
	return leaves
}

// subjectAt names a location the way wrongTypeError does: inputs[0].format.
func subjectAt(location []string) string {
	var subject strings.Builder
	subject.WriteString(configFileName)
	for i, segment := range location {
		switch {
		case isIndex(segment):
			subject.WriteString("[" + segment + "]")
		case i == 0:
			subject.WriteString(": " + segment)
		default:
			subject.WriteString("." + segment)
		}
	}
	return subject.String()
}

func isIndex(segment string) bool {
	return segment != "" && strings.Trim(segment, "0123456789") == ""
}
