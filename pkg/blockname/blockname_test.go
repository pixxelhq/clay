package blockname

import "testing"

func TestParse(t *testing.T) {
	tests := []struct {
		input string
		want  Names
	}{
		{"my-block", Names{"my-block", "my_block", "MyBlock"}},
		{"my_block", Names{"my-block", "my_block", "MyBlock"}},
		{"My-Block", Names{"my-block", "my_block", "MyBlock"}},
		{"MyBlock", Names{"my-block", "my_block", "MyBlock"}},
		{"myBlock", Names{"my-block", "my_block", "MyBlock"}},
		{"myblock", Names{"myblock", "myblock", "Myblock"}},
		{"Resnet50Block", Names{"resnet50-block", "resnet50_block", "Resnet50Block"}},
		{"weather", Names{"weather", "weather", "Weather"}},
		{"w", Names{"w", "w", "W"}},
		{"resnet50", Names{"resnet50", "resnet50", "Resnet50"}},
		{"block-2", Names{"block-2", "block_2", "Block2"}},
		{"my_cool-block", Names{"my-cool-block", "my_cool_block", "MyCoolBlock"}},
		{"my--block", Names{"my--block", "my__block", "MyBlock"}},
	}
	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got, err := Parse(tt.input)
			if err != nil {
				t.Fatalf("Parse(%q) returned error: %v", tt.input, err)
			}
			if got != tt.want {
				t.Errorf("Parse(%q) = %+v, want %+v", tt.input, got, tt.want)
			}
		})
	}
}

func TestParse_Invalid(t *testing.T) {
	for _, input := range []string{"", "1block", "-block", "_block", "block-", "block_", "my block", "my.block", "bloc👍"} {
		if _, err := Parse(input); err == nil {
			t.Errorf("Parse(%q) expected error, got nil", input)
		}
	}
}
