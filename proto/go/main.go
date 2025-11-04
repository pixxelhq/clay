package datatypes

import (
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"strconv"

	generated "github.com/example/clay/proto/go/generated"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
)

const (
	protoMessageMaxRecursionLimit = 32
)

var (
	ErrFieldNotFound    = errors.New("field_not_found")
	ErrFieldIsUnset     = errors.New("field_is_unset")
	ErrUnknownValueType = errors.New("unknown_value_type")
)

type DataInterface interface {
	IsData()
	MarshalJSON() ([]byte, error)
	UnmarshalJSON(b []byte) error
}

type DataWrapperInterface interface {
	GetFormat() (string, error)
	GetName() (string, error)
	GetType() (string, error)
	GetValue() (string, error)
	GetIsArtifact() bool
	GetAssetSource() (*generated.AssetSource, error)
	GetArea() (*float64, error)
	GetStacUrl() (*string, error)
	SetField(field string, value interface{}) error
	SchemaVersion() string
}

type DataSpecWrapperInterface interface {
	GetFormat() (string, error)
	GetName() (string, error)
	GetType() (string, error)
	GetIsArtifact() bool
	ValidateWithInput(input DataWrapperInterface) error
	SchemaVersion() string
}

type InternalFieldDescriptor struct {
	Fd        protoreflect.FieldDescriptor
	Message   protoreflect.Message
	ParentIFD *InternalFieldDescriptor
	IsSet     bool
}

type DataWrapper struct {
	Pb          protoreflect.Message
	FieldRefMap map[string]*InternalFieldDescriptor
}
type DataSpecWrapper struct {
	Pb protoreflect.Message
}

func (d DataWrapper) MarshalJSON() ([]byte, error) {
	return marshalJSON(d.Pb)
}

func (d *DataWrapper) UnmarshalJSON(b []byte) error {
	return unmarshalJSON(b, d.Pb)
}

func (d DataWrapper) GetFormat() (string, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("format")
	if f == nil {
		return "", ErrFieldNotFound
	}
	v := d.Pb.Get(f).Interface().(protoreflect.EnumNumber)
	return generated.Format_name[int32(v)], nil
}

func (d DataWrapper) GetType() (string, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("type")
	if f == nil {
		return "", ErrFieldNotFound
	}
	if !d.Pb.Has(f) {
		return "", ErrFieldIsUnset
	}
	v := d.Pb.Get(f).Interface().(string)
	return v, nil
}

func (d DataWrapper) GetName() (string, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("name")
	if f == nil {
		return "", ErrFieldNotFound
	}
	if !d.Pb.Has(f) {
		return "", ErrFieldIsUnset
	}
	v := d.Pb.Get(f).Interface().(string)
	return v, nil
}

func (d DataWrapper) GetValue() (string, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("value")
	if f == nil {
		return "", ErrFieldNotFound
	}
	if !d.Pb.Has(f) {
		return "", ErrFieldIsUnset
	}
	v := d.Pb.Get(f).Interface().(string)
	return v, nil
}

func (d DataWrapper) GetIsArtifact() bool {
	f := d.Pb.Descriptor().Fields().ByTextName("is_artifact")
	v := d.Pb.Get(f).Interface().(bool)
	return v
}

func (d DataWrapper) SetField(fieldPath string, value interface{}) error {
	fieldRef, ok := d.FieldRefMap[fieldPath]
	if !ok {
		return ErrFieldNotFound
	}

	if !fieldRef.IsSet {
		initNestedFields(fieldRef, d.FieldRefMap, 1)
	}

	// If the parent message was set in a previous operation, we need to get the current message reference
	// because the fieldRef.ParentIFD.Message might be stale (pointing to the old zero-valued message)
	currentParentMessage := fieldRef.ParentIFD.Message
	if fieldRef.ParentIFD.Fd != nil && fieldRef.ParentIFD.ParentIFD != nil {
		// Navigate from the root to get the actual current parent message
		currentParentMessage = fieldRef.ParentIFD.ParentIFD.Message.Get(fieldRef.ParentIFD.Fd).Message()
	}

	protoValue, err := convertToProtoValue(value, currentParentMessage, fieldRef.Fd)

	if err != nil {
		return err
	}

	currentParentMessage.Set(fieldRef.Fd, protoValue)
	fieldRef.IsSet = true

	// If this is a message field, update the message reference for child fields
	if fieldRef.Fd.Kind() == protoreflect.MessageKind && !fieldRef.Fd.IsMap() && !fieldRef.Fd.IsList() {
		updateChildMessageReferences(fieldPath, currentParentMessage.Get(fieldRef.Fd).Message(), d.FieldRefMap)
	}

	return nil
}

func (d DataWrapper) GetStacUrl() (*string, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("stac_url")
	if f == nil {
		return nil, ErrFieldNotFound
	}

	if !d.Pb.Has(f) {
		return nil, ErrFieldIsUnset
	}

	v := d.Pb.Get(f).Interface().(string)
	return &v, nil
}

func (d DataWrapper) GetAssetSource() (*generated.AssetSource, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("asset_source")
	if f == nil {
		return nil, ErrFieldNotFound
	}
	if !d.Pb.Has(f) {
		return nil, ErrFieldIsUnset
	}

	msgVal := d.Pb.Get(f).Message()
	assetSource := &generated.AssetSource{}
	proto.Merge(assetSource, msgVal.Interface().(proto.Message))

	return assetSource, nil
}

func (d DataWrapper) GetArea() (*float64, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("area")
	if f == nil {
		return nil, ErrFieldNotFound
	}

	// add d.Pb.Has post moving area to optional
	v := d.Pb.Get(f).Interface().(float64)
	return &v, nil
}

func (d DataWrapper) SchemaVersion() string {
	f := d.Pb.Descriptor().Fields().ByTextName("version")
	if f == nil {
		return ""
	}
	//if !d.Pb.Has(f) {
	//	return ""
	//}
	v := d.Pb.Get(f).Interface().(protoreflect.EnumNumber)
	return generated.Version_name[int32(v)]
}

func NewDataWrapper(pb protoreflect.Message) DataWrapper {
	fields := pb.Descriptor().Fields()
	for i := 0; i < fields.Len(); i++ {
		fd := fields.Get(i)
		if !pb.Has(fd) && fd.HasDefault() {
			pb.Set(fd, fd.Default())
		}
	}

	m := map[string]*InternalFieldDescriptor{}
	topLevelIFD := InternalFieldDescriptor{Fd: nil, Message: pb, ParentIFD: nil, IsSet: true}
	fieldRefMap := buildProtoFieldReferenceMap(pb, "", m, &topLevelIFD, 1)
	return DataWrapper{Pb: pb, FieldRefMap: fieldRefMap}
}

func (d DataSpecWrapper) MarshalJSON() ([]byte, error) {
	return marshalJSON(d.Pb)
}

func (d *DataSpecWrapper) UnmarshalJSON(b []byte) error {
	return unmarshalJSON(b, d.Pb)
}

func (d DataSpecWrapper) GetFormat() (string, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("format")
	if f == nil {
		return "", ErrFieldNotFound
	}
	v := d.Pb.Get(f).Interface().(protoreflect.EnumNumber)
	return generated.Format_name[int32(v)], nil
}

func (d DataSpecWrapper) GetType() (string, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("type")
	if f == nil {
		return "", ErrFieldNotFound
	}
	if !d.Pb.Has(f) {
		return "", ErrFieldIsUnset
	}
	v := d.Pb.Get(f).Interface().(string)
	return v, nil
}

func (d DataSpecWrapper) GetName() (string, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("name")
	if f == nil {
		return "", ErrFieldNotFound
	}
	if !d.Pb.Has(f) {
		return "", ErrFieldIsUnset
	}
	v := d.Pb.Get(f).Interface().(string)
	return v, nil
}

func (d DataSpecWrapper) GetValidation() (map[string]interface{}, error) {
	f := d.Pb.Descriptor().Fields().ByTextName("validation")
	if f == nil {
		return nil, ErrFieldNotFound
	}
	if !d.Pb.Has(f) {
		return nil, ErrFieldIsUnset
	}
	v := d.Pb.Get(f).Interface().(map[string]interface{})
	return v, nil
}

func (d DataSpecWrapper) ValidateWithInput(input DataWrapperInterface) error {

	// Check if validation is there at the first place
	f := d.Pb.Descriptor().Fields().ByTextName("validation")
	if f == nil || !d.Pb.Has(f) {
		return nil
	}
	v := d.Pb.Get(f)

	format, _ := d.GetFormat()
	switch format {
	case generated.Format_raster.String():
		validator := v.Message().Interface().(*generated.RasterValidation)
		return ValidateRaster(input, validator)
	case generated.Format_vector.String():
		validator := v.Message().Interface().(*generated.VectorValidation)
		return ValidateVector(input, validator)
	case generated.Format_tabular.String():
		validator := v.Message().Interface().(*generated.TabularValidation)
		return ValidateTabular(input, validator)
	case generated.Format_date.String():
		validator := v.Message().Interface().(*generated.DateValidation)
		return ValidateDate(input, validator)
	case generated.Format_string.String():
		validator := v.Message().Interface().(*generated.StringValidation)
		return ValidateString(input, validator)
	case generated.Format_number.String():
		validator := v.Message().Interface().(*generated.NumberValidation)
		return ValidateNumber(input, validator)
	default:
		panic(fmt.Errorf("unsupported format: %s", format))
	}
}

func (d DataSpecWrapper) GetIsArtifact() bool {
	f := d.Pb.Descriptor().Fields().ByTextName("is_artifact")
	v := d.Pb.Get(f).Interface().(bool)
	return v
}

func (d DataSpecWrapper) SchemaVersion() string {
	f := d.Pb.Descriptor().Fields().ByTextName("version")
	if f == nil {
		return ""
	}
	//if !d.Pb.Has(f) {
	//	return ""
	//}
	v := d.Pb.Get(f).Interface().(protoreflect.EnumNumber)
	return generated.Version_name[int32(v)]
}

func NewDataSpecWrapper(pb protoreflect.Message) DataSpecWrapper {
	fields := pb.Descriptor().Fields()
	for i := 0; i < fields.Len(); i++ {
		fd := fields.Get(i)
		if !pb.Has(fd) && fd.HasDefault() {
			pb.Set(fd, fd.Default())
		}
	}
	return DataSpecWrapper{Pb: pb}
}

// FromMap Note: we don't want this function to accept an additional parameter
// `format` since that would mean all callers would have to somehow figure out
// format before calling.
func FromMap(m map[string]json.RawMessage) (DataWrapperInterface, error) {
	v, _ := m["format"]

	b, _ := json.Marshal(m)

	var res DataWrapperInterface
	format := string(v)
	switch format {
	case generated.Format_raster.String():
		r := generated.Raster{}
		res := NewDataWrapper(r.ProtoReflect())
		if err := res.UnmarshalJSON(b); err != nil {
			return nil, err
		}
	case generated.Format_vector.String():
		v := generated.Vector{}
		res := NewDataWrapper(v.ProtoReflect())
		if err := res.UnmarshalJSON(b); err != nil {
			return nil, err
		}
	case generated.Format_tabular.String():
		t := generated.Tabular{}
		res := NewDataWrapper(t.ProtoReflect())
		if err := res.UnmarshalJSON(b); err != nil {
			return nil, err
		}
	case generated.Format_date.String():
		d := generated.Date{}
		res := NewDataWrapper(d.ProtoReflect())
		if err := res.UnmarshalJSON(b); err != nil {
			return nil, err
		}
	case generated.Format_number.String():
		n := generated.Number{}
		res := NewDataWrapper(n.ProtoReflect())
		if err := res.UnmarshalJSON(b); err != nil {
			return nil, err
		}
	case generated.Format_string.String():
		s := generated.String{}
		res := NewDataWrapper(s.ProtoReflect())
		if err := res.UnmarshalJSON(b); err != nil {
			return nil, err
		}
	}
	return res, nil
}

func marshalJSON(m protoreflect.Message) ([]byte, error) {
	marshaler := protojson.MarshalOptions{
		UseEnumNumbers: false, EmitUnpopulated: true, UseProtoNames: true, EmitDefaultValues: true,
	}
	return marshaler.Marshal(m.Interface())
}

func unmarshalJSON(b []byte, m protoreflect.Message) error {
	err := protojson.UnmarshalOptions{DiscardUnknown: true}.Unmarshal(b, m.Interface())
	if err != nil {
		return err
	}
	return nil
}

func ValidateRaster(input DataWrapperInterface, validator *generated.RasterValidation) error {

	name, _ := input.GetName()
	area, err := input.GetArea()
	if err != nil {
		return err
	}

	if validator.MinArea != nil && *validator.MinArea > *area {
		return fmt.Errorf("%s input is less than min area", name)
	}
	if validator.MaxArea != nil && *validator.MaxArea < *area {
		return fmt.Errorf("%s input is greater than max area", name)
	}

	// This is for backward compatibility. If value field is given preference over stac_url field
	value, vErr := input.GetValue()
	if value != "" {
		return nil
	}

	_, err = input.GetStacUrl()
	if err != nil {
		return fmt.Errorf("%s input must have valid value (err: %v) or stac_url field (err: %v)", name, vErr, err)
	}

	return nil
}

func ValidateVector(input DataWrapperInterface, validator *generated.VectorValidation) error {
	name, _ := input.GetName()
	area, err := input.GetArea()
	if err != nil {
		return err
	}
	if validator.MinArea != nil && *validator.MinArea > *area {
		return fmt.Errorf("%s input is less than min area", name)
	}
	if validator.MaxArea != nil && *validator.MaxArea < *area {
		return fmt.Errorf("%s input is greater than max area", name)
	}
	return nil
}

func ValidateTabular(_ DataWrapperInterface, _ *generated.TabularValidation) error {
	return nil
}

func ValidateDate(_ DataWrapperInterface, _ *generated.DateValidation) error {
	return nil
}

func ValidateString(input DataWrapperInterface, validator *generated.StringValidation) error {
	name, _ := input.GetName()
	v, err := input.GetValue()
	if err != nil {
		return err
	}
	if validator.RegexMatch != nil {
		regex, err := regexp.Compile(*validator.RegexMatch)
		if err != nil {
			return fmt.Errorf("invalid regex pattern: %w", err)
		}
		if !regex.MatchString(v) {
			return fmt.Errorf("input %s value does not match regex pattern", name)
		}
	}
	return nil
}

func ValidateNumber(input DataWrapperInterface, validator *generated.NumberValidation) error {
	if validator.MinValue == nil || validator.MaxValue == nil {
		return nil
	}
	v, err := input.GetValue()
	if err != nil {
		return err
	}

	value, err := parseNumber(v)
	if err != nil {
		return err
	}

	if value > *validator.MaxValue || value < *validator.MinValue {
		return fmt.Errorf("value %s is not in range", v)
	}
	return nil
}

func parseNumber(value string) (float64, error) {
	// Try parsing as integer first
	if intVal, err := strconv.ParseInt(value, 10, 64); err == nil {
		return float64(intVal), nil
	}

	// If integer parsing fails, try float
	floatVal, err := strconv.ParseFloat(value, 64)
	if err != nil {
		return 0, fmt.Errorf("value '%s' is neither a valid integer nor float", value)
	}
	return floatVal, nil
}

func buildProtoFieldReferenceMap(message protoreflect.Message, prefix string, fieldRefMap map[string]*InternalFieldDescriptor, parentIFD *InternalFieldDescriptor, recurLevel int) map[string]*InternalFieldDescriptor {
	if recurLevel == protoMessageMaxRecursionLimit {
		panic(fmt.Sprintf("Max recursion limit reached during proto message reference map build."))
	}
	path := ""
	fieldName := ""
	fields := message.Descriptor().Fields()

	var currMessage protoreflect.Message
	for i := 0; i < fields.Len(); i++ {
		f := fields.Get(i)
		fieldName = string(f.Name())
		path = fieldName
		if prefix != "" {
			path = fmt.Sprintf("%s.%s", prefix, path)
		}

		isFieldSet := message.Has(f)

		if f.Kind() == protoreflect.MessageKind && !f.IsMap() && !f.IsList() {
			currMessage = message.Get(f).Message()
		}
		currentIFD := InternalFieldDescriptor{Fd: f, Message: currMessage, ParentIFD: parentIFD, IsSet: isFieldSet}
		fieldRefMap[path] = &currentIFD

		if f.Kind() == protoreflect.MessageKind && !f.IsMap() && !f.IsList() {
			buildProtoFieldReferenceMap(currMessage, path, fieldRefMap, &currentIFD, recurLevel+1)
		}
		currMessage = nil
	}
	return fieldRefMap
}

func convertToProtoValue(value interface{}, msg protoreflect.Message, fd protoreflect.FieldDescriptor) (protoreflect.Value, error) {
	// Handle nil value
	if value == nil {
		return protoreflect.Value{}, nil
	}
	switch fd.Kind() {
	case protoreflect.BoolKind:
		v, ok := value.(bool)
		if !ok {
			return protoreflect.Value{}, fmt.Errorf("expected bool, got %T", value)
		}
		return protoreflect.ValueOfBool(v), nil

	case protoreflect.Int32Kind, protoreflect.Sint32Kind, protoreflect.Sfixed32Kind:
		v, ok := value.(int32)
		if !ok {
			// Try to convert from int
			if intVal, ok := value.(int); ok {
				v = int32(intVal)
			} else {
				return protoreflect.Value{}, fmt.Errorf("expected int32, got %T", value)
			}
		}
		return protoreflect.ValueOfInt32(v), nil

	case protoreflect.Int64Kind, protoreflect.Sint64Kind, protoreflect.Sfixed64Kind:
		v, ok := value.(int64)
		if !ok {
			// Try to convert from int
			if intVal, ok := value.(int); ok {
				v = int64(intVal)
			} else {
				return protoreflect.Value{}, fmt.Errorf("expected int64, got %T", value)
			}
		}
		return protoreflect.ValueOfInt64(v), nil

	case protoreflect.Uint32Kind, protoreflect.Fixed32Kind:
		v, ok := value.(uint32)
		if !ok {
			// Try to convert from uint
			if uintVal, ok := value.(uint); ok {
				v = uint32(uintVal)
			} else {
				return protoreflect.Value{}, fmt.Errorf("expected uint32, got %T", value)
			}
		}
		return protoreflect.ValueOfUint32(v), nil

	case protoreflect.Uint64Kind, protoreflect.Fixed64Kind:
		v, ok := value.(uint64)
		if !ok {
			// Try to convert from uint
			if uintVal, ok := value.(uint); ok {
				v = uint64(uintVal)
			} else {
				return protoreflect.Value{}, fmt.Errorf("expected uint64, got %T", value)
			}
		}
		return protoreflect.ValueOfUint64(v), nil

	case protoreflect.FloatKind:
		v, ok := value.(float32)
		if !ok {
			// Try to convert from float64
			if floatVal, ok := value.(float64); ok {
				v = float32(floatVal)
			} else {
				return protoreflect.Value{}, fmt.Errorf("expected float32, got %T", value)
			}
		}
		return protoreflect.ValueOfFloat32(v), nil

	case protoreflect.DoubleKind:
		v, ok := value.(float64)
		if !ok {
			return protoreflect.Value{}, fmt.Errorf("expected float64, got %T", value)
		}
		return protoreflect.ValueOfFloat64(v), nil

	case protoreflect.StringKind:
		if fd.IsList() {
			if v, ok := value.([]string); ok {
				list := createProtoListFromListOfString(v, msg, fd)
				return protoreflect.ValueOfList(list), nil
			}
			return protoreflect.Value{}, fmt.Errorf("expected []string, got %T", value)
		}
		v, ok := value.(string)
		if !ok {
			return protoreflect.Value{}, fmt.Errorf("expected string, got %T", value)
		}
		return protoreflect.ValueOfString(v), nil

	case protoreflect.BytesKind:
		v, ok := value.([]byte)
		if !ok {
			return protoreflect.Value{}, fmt.Errorf("expected []byte, got %T", value)
		}
		return protoreflect.ValueOfBytes(v), nil

	case protoreflect.EnumKind:
		var enumValue protoreflect.EnumNumber
		switch v := value.(type) {
		case int32:
			enumValue = protoreflect.EnumNumber(v)
		case int:
			enumValue = protoreflect.EnumNumber(v)
		case protoreflect.EnumNumber:
			enumValue = v
		case string:
			enumDescriptor := fd.Enum()
			enumVal := enumDescriptor.Values().ByName(protoreflect.Name(v))
			if enumVal == nil {
				return protoreflect.Value{}, fmt.Errorf("invalid enum value: %s", v)
			}
			enumValue = enumVal.Number()
		case protoreflect.Enum:
			// Handle proto.Enum interface
			enumValue = protoreflect.EnumNumber(v.Number())
		default:
			return protoreflect.Value{}, fmt.Errorf("expected enum value, got %T", value)
		}
		return protoreflect.ValueOfEnum(enumValue), nil

	case protoreflect.MessageKind:
		// currently, the following conversions are not supported,
		// 1. list of dicts -> repeated list of messages
		switch v := value.(type) {
		case proto.Message:
			return protoreflect.ValueOfMessage(v.ProtoReflect()), nil
		case protoreflect.Message:
			return protoreflect.ValueOfMessage(v), nil
		default:
			return protoreflect.Value{}, fmt.Errorf("expected proto.Message or protoreflect.Message, got %T", value)
		}

	default:
		return protoreflect.Value{}, fmt.Errorf("unsupported field type: %v", fd.Kind())
	}
}

func initNestedFields(ifd *InternalFieldDescriptor, m map[string]*InternalFieldDescriptor, recurLevel int) {
	if recurLevel == protoMessageMaxRecursionLimit {
		panic(fmt.Sprintf("Max recursion limit reached during instatiation of unset fields"))
	}
	if ifd.IsSet {
		return
	}

	// we set the parents first
	if ifd.ParentIFD != nil && !ifd.ParentIFD.IsSet {
		initNestedFields(ifd.ParentIFD, m, recurLevel+1)
	}

	if ifd.Fd.Kind() == protoreflect.MessageKind && !ifd.IsSet {
		zeroValuedMsg := ifd.ParentIFD.Message.Mutable(ifd.Fd).Message()
		ifd.ParentIFD.Message.Set(ifd.Fd, protoreflect.ValueOfMessage(zeroValuedMsg))
		ifd.Message = zeroValuedMsg
		ifd.IsSet = true
	}
}

// updateChildMessageReferences updates the Message reference in all child field descriptors
// when a parent message field is set to a new value
func updateChildMessageReferences(parentPath string, newMessage protoreflect.Message, fieldRefMap map[string]*InternalFieldDescriptor) {
	prefix := parentPath + "."
	fields := newMessage.Descriptor().Fields()

	for i := 0; i < fields.Len(); i++ {
		fd := fields.Get(i)
		fieldPath := prefix + string(fd.Name())

		if ifd, exists := fieldRefMap[fieldPath]; exists {
			// Update the message reference to point to the new parent message
			ifd.Message = newMessage

			// If this field is also a message and is set, recursively update its children
			if fd.Kind() == protoreflect.MessageKind && !fd.IsMap() && !fd.IsList() && newMessage.Has(fd) {
				childMessage := newMessage.Get(fd).Message()
				updateChildMessageReferences(fieldPath, childMessage, fieldRefMap)
			}
		}
	}
}
