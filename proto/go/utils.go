package datatypes

import (
	"fmt"
	"reflect"

	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/reflect/protoreflect"
)

func compareLegacyAndProtoTypeMaps(
	legacy map[string]interface{},
	proto map[string]interface{},
	parentKey string,
	ignoreDictFields map[string]struct{},
	onlyCheckFields map[string]struct{},
) bool {
	allFieldsEqual := true

	for key, legacyValue := range legacy {
		fullKeyPath := key
		if parentKey != "" {
			fullKeyPath = parentKey + "." + key
		}

		if _, ignore := ignoreDictFields[fullKeyPath]; ignore {
			continue
		}

		if onlyCheckFields != nil {
			if _, check := onlyCheckFields[fullKeyPath]; !check {
				continue
			}
		}

		protoValue, exists := proto[key]
		if !exists {
			allFieldsEqual = false
			break
		}

		if legacyMap, ok := legacyValue.(map[string]interface{}); ok {
			if protoMap, ok := protoValue.(map[string]interface{}); ok {
				cmpResult := compareLegacyAndProtoTypeMaps(legacyMap, protoMap, fullKeyPath, ignoreDictFields, onlyCheckFields)
				if !cmpResult {
					allFieldsEqual = false
					break
				}
			} else {
				allFieldsEqual = false
				break
			}
		} else {
			if !reflect.DeepEqual(legacyValue, protoValue) {
				allFieldsEqual = false
				break
			}
		}
	}

	return allFieldsEqual
}

// NOTE: this could be a performance hit
func createProtoListFromListOfString(values []string, msg protoreflect.Message, fd protoreflect.FieldDescriptor) protoreflect.List {
	// Handle list creation for a parent message that may not be fully initialized
	var newList protoreflect.List
	if msg.IsValid() {
		newList = msg.Mutable(fd).List()
		newList.Truncate(0)
	} else {
		// For invalid message, create a new list directly
		newList = protoreflect.ValueOf(reflect.ValueOf([]string{}).Interface()).List()
	}

	for _, v := range values {
		newList.Append(protoreflect.ValueOfString(v))
	}
	return newList
}
func printProtoMessage(msg protoreflect.Message) {
	marshaler := protojson.MarshalOptions{
		Multiline:      true,  // Makes output pretty-printed
		Indent:         "  ",  // Sets indentation
		UseEnumNumbers: false, // Use enum names instead of numbers
	}
	b, _ := marshaler.Marshal(msg.Interface())
	fmt.Println(string(b))
}

// PrintProtoValue prints the contents of a protoreflect.Value based on its kind
// PrintProtoStringList prints the contents of a protoreflect.Value that is a list of strings
func PrintProtoStringList(value protoreflect.Value) {
	if !value.IsValid() {
		fmt.Println("Invalid value")
		return
	}

	if !value.List().IsValid() {
		fmt.Println("Not a list value")
		return
	}

	list := value.List()
	fmt.Printf("String List (length: %d):\n", list.Len())
	for i := 0; i < list.Len(); i++ {
		item := list.Get(i)
		fmt.Printf("  [%d]: %q\n", i, item.String())
	}
}
