package datatypes

import (
	"encoding/json"
	"errors"
	"fmt"
	"testing"

	"github.com/example/clay/proto/go/generated"
	"github.com/stretchr/testify/assert"
	"google.golang.org/protobuf/reflect/protoreflect"
)

/*
func Test_LegacyAndProtoTypeMarshalEquality(t *testing.T) {
	dummyDiscreteViz := data.DiscreteViz(map[string]string{"1": "2"})
	dummyValue := "123"
	dummySatelliteLookAngle := 2.3
	dummySunElevationAngle := 2.5
	testcases := []struct {
		Name            string
		LegacyType      data.DataInterface
		ProtoType       func() DataWrapperInterface
		OnlyCheckFields map[string]struct{}
		IgnoreFields    map[string]struct{}
	}{
		{
			Name: "raster-all-but-properties-unset",
			LegacyType: data.Raster{
				DataMeta: data.DataMeta{
					FormatMeta: data.FormatMeta{Format: "raster"},
					TypeMeta: data.TypeMeta{
						Type:        "url",
						Name:        "raster",
						DisplayName: "Raster",
						Description: "some-description",
						IsArtifact:  true,
						Metadata:    map[string]string{"meta": "data"},
						Group:       "group",
					},
					Value: data.Str("123"),
				},
				Area:        420.420,
				AssetSource: data.AssetSource{Id: "id", Identifier: "identifier", Type: "atlas"},
			},
			ProtoType: func() DataWrapperInterface {
				r := generated.Raster{
					Format:      generated.Format_raster,
					Type:        "url",
					Name:        "raster",
					DisplayName: "Raster",
					Description: "some-description",
					IsArtifact:  true,
					Metadata:    map[string]string{"meta": "data"},
					Group:       "group",
					Value:       "123",
					Area:        420.420,
					AssetSource: &generated.AssetSource{Id: "id", Identifier: "identifier", Type: "atlas"},
				}
				return DataWrapper{Pb: r.ProtoReflect()}
			},
			OnlyCheckFields: nil,
			IgnoreFields:    map[string]struct{}{"version": {}, "properties": {}},
		},
		{
			Name: "all-fields-set-raster",
			LegacyType: data.Raster{
				DataMeta: data.DataMeta{
					FormatMeta: data.FormatMeta{Format: "raster"},
					TypeMeta: data.TypeMeta{
						Type:        "url",
						Name:        "raster",
						DisplayName: "Raster",
						Description: "some-description",
						IsArtifact:  true,
						Metadata:    map[string]string{"meta": "data"},
						Group:       "group",
					},
					Value: data.Str("some-value"),
				},
				AssetSource: data.AssetSource{Id: "asset-id", Identifier: "asset-identifier", Type: "atlas"},
				Area:        400.23,
				Properties: data.RasterProperties{
					Collection:         "sentinel-2",
					Source:             "elements",
					Bands:              []string{"B01"},
					Date:               "1-1-1999",
					DType:              "uint8",
					SatelliteLookAngle: 2.3,
					SunElevation:       2.5,
					Images:             []string{"img-1"},
					Visualization: &data.Viz{
						Type:       "continuous",
						Continuous: data.ContinuousViz{ColorMapName: "range", Range: [][]float32{{-1, -2}}},
						Discrete:   &dummyDiscreteViz,
						Bucket: [][]data.BucketViz{
							{
								{
									Range:     []float32{-1, -2},
									ColorCode: "red",
								},
							},
						},
					},
					Discretization: &data.Discretization{
						Type: "index",
						Classes: []data.DiscretizationClass{
							{Color: "red", Name: "grass", Value: &dummyValue, Range: []float32{1, 2}},
						},
					},
				},
			},
			ProtoType: func() DataWrapperInterface {
				r := generated.Raster{
					Version:     generated.Version_v2,
					Format:      generated.Format_raster,
					Type:        "url",
					Name:        "raster",
					DisplayName: "Raster",
					Description: "some-description",
					IsArtifact:  true,
					Metadata:    map[string]string{"meta": "data"},
					Group:       "group",
					Value:       "some-value",time="2025-09-30T09:04:34.038Z" level=info msg="Executor initialized" deadline="0001-01-01 00:00:00 +0000 UTC" includeScriptOutput=false namespace=orchestrator podName=41171b5f-9de1-4ec0-9d9d-25335b40f0eb template=time="2025-09-30T09:04:34.038Z" level=info msg="Executor initialized" deadline="0001-01-01 00:00:00 +0000 UTC" includeScriptOutput=false namespace=orchestrator podName=41171b5f-9de1-4ec0-9d9d-25335b40f0eb template=time="2025-09-30T09:04:34.038Z" level=info msg="Executor initialized" deadline="0001-01-01 00:00:00 +0000 UTC" includeScriptOutput=false namespace=orchestrator podName=41171b5f-9de1-4ec0-9d9d-25335b40f0eb template=time="2025-09-30T09:04:34.038Z" level=info msg="Executor initialized" deadline="0001-01-01 00:00:00 +0000 UTC" includeScriptOutput=false namespace=orchestrator podName=41171b5f-9de1-4ec0-9d9d-25335b40f0eb template=time="2025-09-30T09:04:34.038Z" level=info msg="Executor initialized" deadline="0001-01-01 00:00:00 +0000 UTC" includeScriptOutput=false namespace=orchestrator podName=41171b5f-9de1-4ec0-9d9d-25335b40f0eb template=time="2025-09-30T09:04:34.038Z" level=info msg="Executor initialized" deadline="0001-01-01 00:00:00 +0000 UTC" includeScriptOutput=false namespace=orchestrator podName=41171b5f-9de1-4ec0-9d9d-25335b40f0eb template=
					Area:        400.23,
					AssetSource: &generated.AssetSource{Id: "asset-id", Identifier: "asset-identifier", Type: "atlas"},
					Properties: &generated.RasterProperties{
						Bands:              []string{"B01"},
						Collection:         "sentinel-2",
						Source:             "elements",
						Date:               "1-1-1999",
						Dtype:              "uint8",
						SunElevation:       &dummySunElevationAngle,
						SatelliteLookAngle: &dummySatelliteLookAngle,
						Images:             []string{"img-1"},
						Visualisation: &generated.Visualization{
							Type: generated.VizTypes_continuous,
							Continuous: &generated.ContinuousViz{
								ColorMapName:  "range",
								BandwiseRange: []*generated.Range{{Min: -1, Max: -2}},
							},
							Bucket: &generated.BucketViz{
								Bandwise: []*generated.ListOfBuckets{
									{
										Items: []*generated.Bucket{
											{ColorCode: "red", Min: -1, Max: -2},
										},
									},
								},
							},
						},
						Discretization: &generated.Discretization{
							Type:    "index",
							Classes: []*generated.DiscretizationClass{{Color: "red", Name: "grass", Value: "123"}},
						},
					},
				}
				return DataWrapper{Pb: r.ProtoReflect()}
			},
			OnlyCheckFields: nil,
			IgnoreFields:    map[string]struct{}{"version": {}, "properties.visualisation": {}, "properties.discretization": {}},
		},
	}

	for _, tc := range testcases {
		legacyBytes, err := json.Marshal(tc.LegacyType)
		if err != nil {
			t.Error(err)
			t.FailNow()
		}
		protoBytes, err := json.Marshal(tc.ProtoType())
		if err != nil {
			t.Error(err)
			t.FailNow()
		}

		legacyMap := map[string]interface{}{}
		protoMap := map[string]interface{}{}
		if err := json.Unmarshal(legacyBytes, &legacyMap); err != nil {
			t.Error(err)
			t.FailNow()
		}
		if err := json.Unmarshal(protoBytes, &protoMap); err != nil {
			t.Error(err)
			t.FailNow()
		}

		equal := compareLegacyAndProtoTypeMaps(legacyMap, protoMap, "", tc.IgnoreFields, tc.OnlyCheckFields)
		if !equal {
			t.Errorf("%s: not equal", tc.Name)
			t.Fail()
		}
	}
}

func Test_DataWrapper_GetFormat(t *testing.T) {
	r := generated.Raster{Format: generated.Format_date}
	dw := DataWrapper{Pb: r.ProtoReflect()}

	s, err := dw.GetFormat()
	if err != nil || s != "date" {
		t.Errorf(
			"failed: expected: %+v, %+v; got: %+v, %+v", nil, "date", err, s,
		)
	}
	r = generated.Raster{}
	dw = DataWrapper{Pb: r.ProtoReflect()}
	v := dw.SchemaVersion()
	if v != generated.Version_v2.String() {
		t.Errorf("failed schema version: expected: %s, got: %s", "v2", v)
	}
}

func Test_DataWrapper_GetIsArtifact(t *testing.T) {
	r := generated.Raster{Format: generated.Format_date, IsArtifact: true}
	dw := DataWrapper{Pb: r.ProtoReflect()}
	s := dw.GetIsArtifact()
	if s != true {
		t.Errorf("incorrect return value. expected: %v, got: %v", r.IsArtifact, s)
	}
}

func Test_DataSpecWrapper_Validate(t *testing.T) {
	tests := []struct {
		name     string
		spec     func() *DataSpecWrapper
		input    func() *DataWrapper
		errIsNil bool
	}{
		{
			name: "base valid case",
			spec: func() *DataSpecWrapper {
				maxArea := float64(1000)
				minArea := float64(10)
				rs := generated.RasterSpec{
					Format: generated.Format_raster,
					Validation: &generated.RasterValidation{
						MinArea: &minArea,
						MaxArea: &maxArea,
					},
				}
				return &DataSpecWrapper{Pb: rs.ProtoReflect()}
			},
			input: func() *DataWrapper {
				testRaster := generated.Raster{
					Format: generated.Format_raster,
					Area:   1200,
				}
				return &DataWrapper{Pb: testRaster.ProtoReflect()}

			},
			errIsNil: false,
		},
		{
			name: "base failed validation case",
			spec: func() *DataSpecWrapper {
				maxArea := float64(1000)
				minArea := float64(10)
				rs := generated.RasterSpec{
					Format: generated.Format_raster,
					Validation: &generated.RasterValidation{
						MinArea: &minArea,
						MaxArea: &maxArea,
					},
				}
				return &DataSpecWrapper{Pb: rs.ProtoReflect()}
			},
			input: func() *DataWrapper {
				testRaster := generated.Raster{
					Format: generated.Format_raster,
					Area:   200,
				}
				return &DataWrapper{Pb: testRaster.ProtoReflect()}

			},
			errIsNil: true,
		},
		{
			name: "base succeess, one param is nil validation case",
			spec: func() *DataSpecWrapper {
				maxArea := float64(1000)
				rs := generated.RasterSpec{
					Format: generated.Format_raster,
					Validation: &generated.RasterValidation{
						MinArea: nil,
						MaxArea: &maxArea,
					},
				}
				return &DataSpecWrapper{Pb: rs.ProtoReflect()}
			},
			input: func() *DataWrapper {
				testRaster := generated.Raster{
					Format: generated.Format_raster,
					Area:   200,
				}
				return &DataWrapper{Pb: testRaster.ProtoReflect()}

			},
			errIsNil: true,
		},
	}

	for _, tc := range tests {
		s := tc.spec()
		d := tc.input()
		err := s.ValidateWithInput(*d)
		if (tc.errIsNil == true && err != nil) || (tc.errIsNil == false && err == nil) {
			t.Errorf(
				"tc.name: %s, errIsNil: %v, got: %v", tc.name, tc.errIsNil, err,
			)
			t.FailNow()
		}
	}
}
*/

func Test_Unmarshal_WithDefaults(t *testing.T) {
	testM := map[string]interface{}{
		"name":   "r",
		"format": "vector",
	}

	b, _ := json.Marshal(testM)

	r := generated.Vector{}
	dw := DataWrapper{Pb: r.ProtoReflect()}

	f, err := dw.GetFormat()
	if err != nil {
		t.Error(err)
		t.FailNow()
	}
	if f != "vector" {
		t.Errorf("fromat")
	}

	err = json.Unmarshal(b, &dw)
	if err != nil {
		t.Error(err)
		t.FailNow()
	}

	f, _ = dw.GetFormat()
	if f != "vector" {
		t.Errorf("format unequal; expected %s, found %s", "vector", f)
	}
	if !dw.GetIsArtifact() {
		t.Errorf("`is_artifact` unequal; expected true, found false")
	}
}

func Test_buildProtoFieldReferenceMap_Init(t *testing.T) {
	r := generated.Raster{}
	toCheckFields := []string{"area", "type", "format", "properties.bands", "properties.visualisation.type"}
	refMap := map[string]*InternalFieldDescriptor{}
	got := buildProtoFieldReferenceMap(r.ProtoReflect(), "", refMap, nil, 1)
	if len(got) == 0 {
		t.Error("expected non-empty field map")
	}
	// we don't check for all fields. for sanily's sake, we randomly check for some fields.
	for _, field := range toCheckFields {
		if _, ok := refMap[field]; !ok {
			t.Errorf("field %s not found in reference map", field)
		}
	}
}

func Test_convertToProtoValue(t *testing.T) {
	// Create a test message to get field descriptors
	raster := &generated.Raster{}
	msg := raster.ProtoReflect()

	tests := []struct {
		name      string
		field     protoreflect.FieldDescriptor
		value     interface{}
		expectErr bool
	}{
		{
			name:      "string field",
			field:     msg.Descriptor().Fields().ByName("name"),
			value:     "test",
			expectErr: false,
		},
		{
			name:      "bool field",
			field:     msg.Descriptor().Fields().ByName("is_artifact"),
			value:     true,
			expectErr: false,
		},
		{
			name:      "double field",
			field:     msg.Descriptor().Fields().ByName("area"),
			value:     123.45,
			expectErr: false,
		},
		{
			name:      "enum field as int",
			field:     msg.Descriptor().Fields().ByName("format"),
			value:     int32(0), // Format_raster
			expectErr: false,
		},
		{
			name:      "enum field as string",
			field:     msg.Descriptor().Fields().ByName("format"),
			value:     "vector",
			expectErr: false,
		},
		{
			name:      "wrong type",
			field:     msg.Descriptor().Fields().ByName("name"),
			value:     123,
			expectErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			val, err := convertToProtoValue(tt.value, msg, tt.field)
			if tt.expectErr {
				if err == nil {
					t.Error("expected error but got none")
				}
				return
			}
			if err != nil {
				t.Errorf("unexpected error: %v", err)
				return
			}
			if !val.IsValid() {
				t.Error("converted value is invalid")
			}
		})
	}
}

func Test_ConvertingToProtoValues(t *testing.T) {
	tests := []struct {
		name     string
		input    func() protoreflect.Message
		field    string
		value    interface{}
		expected func() protoreflect.Message
		skip     bool
		err      error
	}{
		{
			name: "string field",
			input: func() protoreflect.Message {
				r := &generated.Raster{}
				return r.ProtoReflect()
			},
			field: "name",
			value: "test",
			expected: func() protoreflect.Message {
				r := &generated.Raster{Name: getRefToString("test")}
				return r.ProtoReflect()
			},
			err: nil,
		},
		{
			name: "bool field",
			input: func() protoreflect.Message {
				r := &generated.Raster{}
				return r.ProtoReflect()
			},
			field: "is_artifact",
			value: true,
			expected: func() protoreflect.Message {
				r := &generated.Raster{IsArtifact: getRefToBool(true)}
				return r.ProtoReflect()
			},
			err: nil,
		},
		{
			name: "double field",
			input: func() protoreflect.Message {
				r := &generated.Raster{}
				return r.ProtoReflect()
			},
			field: "area",
			value: 123.45,
			expected: func() protoreflect.Message {
				r := &generated.Raster{Area: getRefToF64(123.45)}
				return r.ProtoReflect()
			},
			err: nil,
		},
		{
			name: "enum field as int",
			input: func() protoreflect.Message {
				r := &generated.Raster{}
				return r.ProtoReflect()
			},
			field: "format",
			value: int32(0),
			expected: func() protoreflect.Message {
				r := &generated.Raster{Format: getRefToFormat(generated.Format_raster)}
				return r.ProtoReflect()
			},
			err: nil,
		},
		{
			name: "enum field as string",
			input: func() protoreflect.Message {
				r := &generated.Raster{}
				return r.ProtoReflect()
			},
			field: "format",
			value: "vector",
			expected: func() protoreflect.Message {
				r := &generated.Raster{Format: getRefToFormat(generated.Format_vector)}
				return r.ProtoReflect()
			},
			err: nil,
		},
		{
			name: "wrong type",
			input: func() protoreflect.Message {
				r := &generated.Raster{}
				return r.ProtoReflect()
			},
			field: "name",
			value: 123,
			expected: func() protoreflect.Message {
				r := &generated.Raster{}
				return r.ProtoReflect()
			},
			err: errors.New("expected string, got int"),
		},
		{
			name: "convert []string",
			input: func() protoreflect.Message {
				rp := &generated.RasterProperties{}
				return rp.ProtoReflect()
			},
			field: "bands",
			value: []string{"1", "2"},
			expected: func() protoreflect.Message {
				rp := &generated.RasterProperties{
					Bands: []string{"1", "2"},
				}
				return rp.ProtoReflect()
			},
			err: nil,
		},
		{
			name: "convert int to format enum",
			input: func() protoreflect.Message {
				v := generated.Raster{}
				return v.ProtoReflect()
			},
			field: "format",
			value: int32(3),
			expected: func() protoreflect.Message {
				r := &generated.Raster{Format: getRefToFormat(generated.Format_string)}
				return r.ProtoReflect()
			},
			err: nil,
		},
		{
			name: "convert list of range dicts to list of range objects",
			input: func() protoreflect.Message {
				v := generated.ContinuousViz{}
				return v.ProtoReflect()
			},
			field: "bandwise_range",
			value: []map[string]interface{}{{"min": 1.0, "max": 2.5}, {"min": 10.0, "max": 15}},
			expected: func() protoreflect.Message {
				r := &generated.ContinuousViz{BandwiseRange: []*generated.Range{
					{Min: getRefToF32(1.0), Max: getRefToF32(2.5)},
					{Min: getRefToF32(10.0), Max: getRefToF32(15)},
				}}
				return r.ProtoReflect()
			},
			err: errors.New("unsupported field type: message"),
		},
		{
			name: "convert object to message",
			input: func() protoreflect.Message {
				v := generated.DiscretizationClass{}
				return v.ProtoReflect()
			},
			field: "range",
			value: map[string]interface{}{"min": -100, "max": 123},
			expected: func() protoreflect.Message {
				v := generated.DiscretizationClass{Range: &generated.Range{
					Min: getRefToF32(-100),
					Max: getRefToF32(123),
				}}
				return v.ProtoReflect()
			},
			err: errors.New("unsupported field type: message"),
		},
	}

	for _, tt := range tests {
		if tt.skip {
			continue
		}
		msg := tt.input()
		fd := msg.Interface().ProtoReflect().Descriptor().Fields().ByTextName(tt.field)
		pv, err := convertToProtoValue(tt.value, msg, fd)
		if tt.err != nil && err != nil {
			continue
		}

		assert.NoError(t, err)
		expected := tt.expected()
		efd := expected.Interface().ProtoReflect().Descriptor().Fields().ByTextName(tt.field)
		expectedValue := expected.Get(efd)
		assert.True(t, pv.Equal(expectedValue), fmt.Sprintf("%s: expected: %+v, got: %+v", tt.name, expectedValue, pv))
	}
}

func Test_SetField_BasicTypes(t *testing.T) {
	msg := &generated.Raster{}
	wrapper := NewDataWrapper(msg.ProtoReflect())

	tests := []struct {
		name     string
		field    string
		value    interface{}
		expected interface{}
		hasError bool
	}{
		{
			name:     "set string field",
			field:    "name",
			value:    "new-name",
			expected: "new-name",
		},
		{
			name:     "set bool field",
			field:    "is_artifact",
			value:    true,
			expected: true,
		},
		{
			name:     "invalid field",
			field:    "nonexistent_field",
			value:    "test",
			hasError: true,
		},
		{
			name:     "type mismatch",
			field:    "description",
			value:    123,
			hasError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := wrapper.SetField(tt.field, tt.value)
			if tt.hasError {
				assert.Error(t, err)
				return
			}
			assert.NoError(t, err)

			// Get the field value dynamically
			fd, exists := wrapper.FieldRefMap[tt.field]
			assert.True(t, exists)

			// Get the value using reflection
			val := msg.ProtoReflect().Get(fd.Fd).Interface()
			assert.Equal(t, tt.expected, val)

		})
	}
}

func Test_SetField_NestedMessage(t *testing.T) {
	msg := &generated.Raster{}
	wrapper := NewDataWrapper(msg.ProtoReflect())

	tests := []struct {
		name      string
		field     string
		value     interface{}
		expected  interface{}
		validator func() bool
	}{
		{
			name:  "set nested []string field",
			field: "properties.bands",
			value: []string{"B01", "B02"},
			validator: func() bool {
				if len(msg.Properties.Bands) != 2 || msg.Properties.Bands[0] != "B01" || msg.Properties.Bands[1] != "B02" {
					return false
				}
				return true
			},
		},
		{
			name:  "set nested f64 field",
			field: "properties.sun_elevation",
			value: 120.23,
			validator: func() bool {
				return *msg.Properties.SunElevation == 120.23
			},
		}, {
			name:  "set nested f64 field",
			field: "properties.sun_elevation",
			value: 240.46,
			validator: func() bool {
				return *msg.Properties.SunElevation == 240.46
			},
		},
		{
			name:  "set discrete viz",
			field: "properties.visualisation",
			value: &generated.Visualization{Type: generated.VizTypes_discrete.Enum(), Discrete: map[string]string{"label": "color"}},
			validator: func() bool {
				return msg.Properties.Visualisation != nil && len(msg.Properties.Visualisation.Discrete) == 1
			},
		},
		{
			name:  "set discrete descretization",
			field: "properties.discretization",
			value: &generated.Discretization{Type: getRefToString("index"), Classes: []*generated.DiscretizationClass{
				{
					Name:  getRefToString("grass"),
					Color: getRefToString("red"),
					Value: getRefToString("1"),
					Range: &generated.Range{Min: getRefToF32(1), Max: getRefToF32(2)},
				},
				{
					Name:  getRefToString("land"),
					Color: getRefToString("blue"),
					Value: getRefToString("2"),
					Range: &generated.Range{Min: getRefToF32(100), Max: getRefToF32(200)},
				},
			}},
			validator: func() bool {
				return msg.Properties.Discretization != nil &&
					msg.Properties.Discretization.Type != nil && *msg.Properties.Discretization.Type == "index" &&
					len(msg.Properties.Discretization.Classes) == 2 &&
					*msg.Properties.Discretization.Classes[0].Name == "grass" &&
					*msg.Properties.Discretization.Classes[0].Color == "red" &&
					*msg.Properties.Discretization.Classes[0].Value == "1" &&
					msg.Properties.Discretization.Classes[0].Range != nil &&
					*msg.Properties.Discretization.Classes[0].Range.Min == 1 &&
					*msg.Properties.Discretization.Classes[0].Range.Max == 2 &&
					*msg.Properties.Discretization.Classes[1].Name == "land" &&
					*msg.Properties.Discretization.Classes[1].Color == "blue" &&
					*msg.Properties.Discretization.Classes[1].Value == "2" &&
					msg.Properties.Discretization.Classes[1].Range != nil &&
					*msg.Properties.Discretization.Classes[1].Range.Min == 100 &&
					*msg.Properties.Discretization.Classes[1].Range.Max == 200
			},
		},
		{
			name:  "set source",
			field: "properties.source",
			value: "pixxel",
			validator: func() bool {
				return msg.Properties != nil && *msg.Properties.Source == "pixxel"
			},
		},
		{
			name:  "set discretization type only",
			field: "properties.discretization.type",
			value: "value",
			validator: func() bool {
				return msg.Properties != nil && *msg.Properties.Discretization.Type == "value"
			},
		},
		{
			name:  "set discretization type only",
			field: "properties.discretization",
			value: &generated.Discretization{Type: getRefToString("index"), Classes: []*generated.DiscretizationClass{
				{
					Name:  getRefToString("building"),
					Color: getRefToString("blue"),
					Value: getRefToString("2"),
					Range: &generated.Range{Min: getRefToF32(1), Max: getRefToF32(2)},
				},
			}},
			validator: func() bool {
				return msg.Properties != nil &&
					msg.Properties.Discretization != nil &&
					*msg.Properties.Discretization.Type == "index" &&
					len(msg.Properties.Discretization.Classes) == 1 &&
					*msg.Properties.Discretization.Classes[0].Name == "building" &&
					*msg.Properties.Discretization.Classes[0].Color == "blue" &&
					*msg.Properties.Discretization.Classes[0].Value == "2" &&
					msg.Properties.Discretization.Classes[0].Range != nil &&
					*msg.Properties.Discretization.Classes[0].Range.Min == 1 &&
					*msg.Properties.Discretization.Classes[0].Range.Max == 2
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := wrapper.SetField(tt.field, tt.value)
			if !assert.NoError(t, err) {
				t.FailNow()
			}

			// Get the field value dynamically
			ifd, exists := wrapper.FieldRefMap[tt.field]
			if !exists {
				t.Errorf("%s: failing now, ifd not found", tt.name)
				t.FailNow()
			}

			if !assert.True(t, tt.validator(), fmt.Sprintf("%s: validation failed", tt.name)) {
				// debug print
				printProtoMessage(msg.ProtoReflect())
			}

			// sanity checks
			assert.True(t, ifd.ParentIFD.Message.Get(ifd.Fd).IsValid(), fmt.Sprintf("target message is invalid"))
			assert.True(t, ifd.ParentIFD.Message.IsValid(), fmt.Sprintf("parent message is invalid"))
		})
	}
}

func Test_initNestedFields(t *testing.T) {
	_ = []struct {
		name     string
		input    func() *DataWrapper
		validate func() bool
	}{
		{
			name: "setting properties.bands",
			input: func() *DataWrapper {
				rr := generated.Raster{}
				r := NewDataWrapper(rr.ProtoReflect())
				return &r
			},
			validate: func() bool {
				return false
			},
		},
	}
}

func Test_GetStacUrl(t *testing.T) {
	testcases := []struct {
		name        string
		input       func() *DataWrapper
		expectedURL string
		expectErr   bool
	}{
		{
			name: "stac_url is set",
			input: func() *DataWrapper {
				raster := &generated.Raster{
					StacUrl: getRefToString("https://example.com/stac"),
				}
				return &DataWrapper{Pb: raster.ProtoReflect()}
			},
			expectedURL: "https://example.com/stac",
			expectErr:   false,
		},
		{
			name: "stac_url is not set",
			input: func() *DataWrapper {
				raster := &generated.Raster{}
				return &DataWrapper{Pb: raster.ProtoReflect()}
			},
			expectedURL: "",
			expectErr:   true,
		},
	}

	for _, tc := range testcases {
		t.Run(tc.name, func(t *testing.T) {
			dw := tc.input()
			url, err := dw.GetStacUrl()

			if tc.expectErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tc.expectedURL, *url)
			}
		})
	}
}

/*
	func Test_SetField_WholeMessage(t *testing.T) {
		msg := &TestMessage{}
		wrapper := NewDataWrapper(msg)

		nestedMsg := &NestedMessage{
			NestedString: "test nested",
		}

		err := wrapper.SetField("nested_field", nestedMsg)
		assert.NoError(t, err)

		val, err := wrapper.GetField("nested_field")
		assert.NoError(t, err)
		assert.True(t, proto.Equal(nestedMsg, val.(proto.Message)))
	}

	func Test_SetField_NilValue(t *testing.T) {
		msg := &TestMessage{}
		wrapper := NewDataWrapper(msg)

		err := wrapper.SetField("string_field", nil)
		assert.NoError(t, err)

		val, err := wrapper.GetField("string_field")
		assert.NoError(t, err)
		assert.Empty(t, val)
	}
*/
func TestProtobufFieldOverwrite(t *testing.T) {
	// Create a simple message with a string field
	msg := &generated.Discretization{
		Type: new(string),
	}

	// Set initial value
	*msg.Type = "index"

	// Check initial value
	assert.Equal(t, "index", *msg.Type)

	// Set new value
	*msg.Type = "value"

	// Check new value
	assert.Equal(t, "value", *msg.Type)

	// Try setting via reflection
	typeField := msg.ProtoReflect().Descriptor().Fields().ByName("type")
	msg.ProtoReflect().Set(typeField, protoreflect.ValueOfString("another"))

	// Check it was updated
	assert.Equal(t, "another", *msg.Type)
}
func getRefToString(s string) *string {
	return &s
}

func getRefToBool(b bool) *bool {
	return &b
}

func getRefToF64(f float64) *float64 {
	return &f
}

func getRefToF32(f float32) *float32 {
	return &f
}

func getRefToFormat(f generated.Format) *generated.Format {
	return &f
}

func getRefToVizTypes(v generated.VizTypes) *generated.VizTypes {
	return &v
}

func getRefToVersion() *generated.Version {
	v := generated.Version_v2
	return &v
}
