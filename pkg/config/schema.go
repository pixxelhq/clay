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

const (
	specReference  = "https://pixxelhq.github.io/clay/spec/"
	migrationGuide = specReference + "#moving-to-clayv1"
)

//go:embed schema/v1.json
var schemaV1JSON []byte

var schemas = map[string]*jsonschema.Schema{
	"clay/v1": mustCompile("https://pixxelhq.github.io/clay/schema/v1.json", schemaV1JSON),
}

var patternRules = map[string]string{
	"name":    "must start with a lowercase letter, end with a lowercase letter or digit, and use only lowercase letters, digits, '-' and '_'",
	"version": "must be a semantic version without a leading v, such as 1.2.3",
}

func mustCompile(url string, schemaJSON []byte) *jsonschema.Schema {
	doc, err := jsonschema.UnmarshalJSON(bytes.NewReader(schemaJSON))
	if err != nil {
		panic(err)
	}
	compiler := jsonschema.NewCompiler()
	if err := compiler.AddResource(url, doc); err != nil {
		panic(err)
	}
	return compiler.MustCompile(url)
}

func supportedAPIVersions() string {
	versions := make([]string, 0, len(schemas))
	for version := range schemas {
		versions = append(versions, version)
	}
	slices.Sort(versions)
	return strings.Join(versions, ", ")
}

func validate(doc any) error {
	fields, ok := doc.(map[string]any)
	if !ok {
		return fmt.Errorf("%s must be a mapping, not %s\nhint: see the clay.yaml reference: %s", configFileName, jsonKind(doc), specReference)
	}

	apiVersion, ok := fields["apiVersion"]
	if !ok {
		return fmt.Errorf("%s has no apiVersion\nhint: add apiVersion: clay/v1, see %s", configFileName, migrationGuide)
	}
	schema, ok := schemas[fmt.Sprint(apiVersion)]
	if !ok {
		return fmt.Errorf("%s: apiVersion %q is not supported by this version of Clay; supported: %s\n"+
			"hint: to move an older clay.yaml to clay/v1, see %s; for a newer apiVersion, upgrade Clay",
			configFileName, fmt.Sprint(apiVersion), supportedAPIVersions(), migrationGuide)
	}

	err := schema.Validate(doc)
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
	return fmt.Errorf("%s does not match the %s schema:\n  %s\nhint: see the clay.yaml reference: %s",
		configFileName, apiVersion, strings.Join(problems, "\n  "), specReference)
}

func describe(err *jsonschema.ValidationError, printer *message.Printer) string {
	switch k := err.ErrorKind.(type) {
	case *kind.Pattern:
		if len(err.InstanceLocation) == 1 {
			if rule, ok := patternRules[err.InstanceLocation[0]]; ok {
				return rule
			}
		}
	case *kind.Type:
		if k.Got == "number" && slices.Contains(k.Want, "string") {
			return "must be text, not a number; put the value in quotes so that YAML reads it as text"
		}
	}
	return err.ErrorKind.LocalizedString(printer)
}

func jsonKind(v any) string {
	switch v.(type) {
	case nil:
		return "empty"
	case []any:
		return "a list"
	case string:
		return "text"
	case bool:
		return "true or false"
	default:
		return "a number"
	}
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

// subjectAt names a location as inputs[0].format.
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
