package datatypes

import "testing"

func TestCompareLegacyAndProtoTypeMaps(t *testing.T) {
	tests := []struct {
		name             string
		legacy           map[string]interface{}
		proto            map[string]interface{}
		parentKey        string
		ignoreDictFields map[string]struct{}
		onlyCheckFields  map[string]struct{}
		expected         bool
	}{
		{
			name: "equal dictionaries",
			legacy: map[string]interface{}{
				"key1": "value1",
				"key2": map[string]interface{}{
					"subkey1": "subvalue1",
				},
			},
			proto: map[string]interface{}{
				"key1": "value1",
				"key2": map[string]interface{}{
					"subkey1": "subvalue1",
				},
			},
			parentKey:        "",
			ignoreDictFields: map[string]struct{}{},
			onlyCheckFields:  nil,
			expected:         true,
		},
		{
			name: "different dictionaries",
			legacy: map[string]interface{}{
				"key1": "value1",
				"key2": map[string]interface{}{
					"subkey1": "subvalue1",
				},
			},
			proto: map[string]interface{}{
				"key1": "value1",
				"key2": map[string]interface{}{
					"subkey1": "differentSubvalue",
				},
			},
			parentKey:        "",
			ignoreDictFields: map[string]struct{}{},
			onlyCheckFields:  nil,
			expected:         false,
		},
		{
			name: "ignore specific field",
			legacy: map[string]interface{}{
				"key1": "value1",
				"key2": map[string]interface{}{
					"subkey1": "subvalue1",
					"subkey2": "subvalue2",
				},
			},
			proto: map[string]interface{}{
				"key1": "value1",
				"key2": map[string]interface{}{
					"subkey1": "subvalue1",
					"subkey2": "differentSubvalue",
				},
			},
			parentKey: "",
			ignoreDictFields: map[string]struct{}{
				"key2.subkey2": {},
			},
			onlyCheckFields: nil,
			expected:        true,
		},
		{
			name: "only check specific field",
			legacy: map[string]interface{}{
				"key1": "value1",
				"key2": map[string]interface{}{
					"subkey1": "subvalue1",
					"subkey2": "subvalue2",
				},
			},
			proto: map[string]interface{}{
				"key1": "value1",
				"key2": map[string]interface{}{
					"subkey1": "subvalue1",
					"subkey2": "differentSubvalue",
				},
			},
			parentKey:        "",
			ignoreDictFields: map[string]struct{}{},
			onlyCheckFields: map[string]struct{}{
				"key1": {},
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := compareLegacyAndProtoTypeMaps(tt.legacy, tt.proto, tt.parentKey, tt.ignoreDictFields, tt.onlyCheckFields)
			if result != tt.expected {
				t.Errorf("compareLegacyAndProtoDicts() = %v, expected %v", result, tt.expected)
			}
		})
	}
}
