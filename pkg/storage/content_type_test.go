package storage

import (
	"bytes"
	"testing"
)

func TestDetectContentType_ByExtension(t *testing.T) {
	cases := map[string]string{
		"thumbnail.png":   "image/png",
		"sample.jpg":      "image/jpeg",
		"sample.jpeg":     "image/jpeg",
		"walkthrough.mp4": "video/mp4",
		"datasheet.pdf":   "application/pdf",
		"hero.webp":       "image/webp",
		"UPPER.PNG":       "image/png",
	}
	for name, want := range cases {
		t.Run(name, func(t *testing.T) {
			// Body is deliberately not a real file of that type — extension wins.
			got, err := detectContentType(name, bytes.NewReader([]byte("not real bytes")))
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if got != want {
				t.Errorf("detectContentType(%q) = %q, want %q", name, got, want)
			}
		})
	}
}

func TestDetectContentType_MagicBytesFallback(t *testing.T) {
	// No useful extension → fall back to sniffing. PNG magic header.
	png := []byte{0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0, 0, 0, 0}
	r := bytes.NewReader(png)
	got, err := detectContentType("blob", r)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "image/png" {
		t.Errorf("sniffed content type = %q, want image/png", got)
	}
	// Reader must be rewound for the subsequent upload.
	if r.Len() != len(png) {
		t.Errorf("reader not rewound: have %d bytes left, want %d", r.Len(), len(png))
	}
}
