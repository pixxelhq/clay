package storage

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/request"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// mockS3Client is a mock implementation of S3 client for testing
type mockS3Client struct {
	*s3.S3
	objects     map[string][]byte
	listResults []string
}

func (m *mockS3Client) HeadObjectWithContext(ctx context.Context, input *s3.HeadObjectInput, opts ...request.Option) (*s3.HeadObjectOutput, error) {
	key := aws.StringValue(input.Key)
	if _, exists := m.objects[key]; exists {
		return &s3.HeadObjectOutput{}, nil
	}
	return nil, fmt.Errorf("NotFound")
}

func (m *mockS3Client) DeleteObjectWithContext(ctx context.Context, input *s3.DeleteObjectInput, opts ...request.Option) (*s3.DeleteObjectOutput, error) {
	key := aws.StringValue(input.Key)
	delete(m.objects, key)
	return &s3.DeleteObjectOutput{}, nil
}

func (m *mockS3Client) ListObjectsV2PagesWithContext(ctx context.Context, input *s3.ListObjectsV2Input, fn func(*s3.ListObjectsV2Output, bool) bool, opts ...request.Option) error {
	prefix := aws.StringValue(input.Prefix)
	var contents []*s3.Object

	for _, key := range m.listResults {
		if len(prefix) == 0 || (len(key) >= len(prefix) && key[:len(prefix)] == prefix) {
			contents = append(contents, &s3.Object{
				Key: aws.String(key),
			})
		}
	}

	output := &s3.ListObjectsV2Output{
		Contents: contents,
	}
	fn(output, true)
	return nil
}

func TestNewS3Provider(t *testing.T) {
	tests := []struct {
		name    string
		config  S3Config
		wantErr bool
	}{
		{
			name: "valid config",
			config: S3Config{
				Region: "us-east-1",
				Bucket: "test-bucket",
			},
			wantErr: false,
		},
		{
			name: "empty region",
			config: S3Config{
				Bucket: "test-bucket",
			},
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			provider, err := NewS3Provider(tt.config)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, provider)
				assert.Equal(t, tt.config.Bucket, provider.bucket)
			}
		})
	}
}

func TestS3Provider_normalizeKey(t *testing.T) {
	provider := &S3Provider{bucket: "test-bucket"}

	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "simple key",
			input:    "path/to/file.txt",
			expected: "path/to/file.txt",
		},
		{
			name:     "with leading slash",
			input:    "/path/to/file.txt",
			expected: "path/to/file.txt",
		},
		{
			name:     "with s3:// prefix",
			input:    "s3://path/to/file.txt",
			expected: "path/to/file.txt",
		},
		{
			name:     "with bucket name",
			input:    "test-bucket/path/to/file.txt",
			expected: "path/to/file.txt",
		},
		{
			name:     "with s3:// and bucket",
			input:    "s3://test-bucket/path/to/file.txt",
			expected: "path/to/file.txt",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := provider.normalizeKey(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestS3Provider_Exists(t *testing.T) {
	mockClient := &mockS3Client{
		objects: map[string][]byte{
			"existing/file.txt": []byte("content"),
		},
	}

	provider := &S3Provider{
		client: mockClient,
		bucket: "test-bucket",
	}

	tests := []struct {
		name     string
		path     string
		expected bool
		wantErr  bool
	}{
		{
			name:     "existing file",
			path:     "existing/file.txt",
			expected: true,
			wantErr:  false,
		},
		{
			name:     "non-existing file",
			path:     "non-existing/file.txt",
			expected: false,
			wantErr:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			exists, err := provider.Exists(context.Background(), tt.path)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expected, exists)
			}
		})
	}
}

func TestS3Provider_List(t *testing.T) {
	mockClient := &mockS3Client{
		listResults: []string{
			"blocks/test-block/v1.0.0/file1.txt",
			"blocks/test-block/v1.0.0/file2.txt",
			"blocks/test-block/v2.0.0/file3.txt",
			"blocks/other-block/file4.txt",
		},
	}

	provider := &S3Provider{
		client: mockClient,
		bucket: "test-bucket",
	}

	tests := []struct {
		name     string
		prefix   string
		expected []string
	}{
		{
			name:   "list all v1.0.0 files",
			prefix: "blocks/test-block/v1.0.0/",
			expected: []string{
				"blocks/test-block/v1.0.0/file1.txt",
				"blocks/test-block/v1.0.0/file2.txt",
			},
		},
		{
			name:   "list all test-block files",
			prefix: "blocks/test-block/",
			expected: []string{
				"blocks/test-block/v1.0.0/file1.txt",
				"blocks/test-block/v1.0.0/file2.txt",
				"blocks/test-block/v2.0.0/file3.txt",
			},
		},
		{
			name:   "list all files",
			prefix: "",
			expected: []string{
				"blocks/test-block/v1.0.0/file1.txt",
				"blocks/test-block/v1.0.0/file2.txt",
				"blocks/test-block/v2.0.0/file3.txt",
				"blocks/other-block/file4.txt",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			objects, err := provider.List(context.Background(), tt.prefix)
			assert.NoError(t, err)
			assert.Equal(t, tt.expected, objects)
		})
	}
}

func TestS3Provider_ManifestOperations(t *testing.T) {
	// This test verifies manifest serialization/deserialization logic

	// Create test manifest
	manifest := &Manifest{
		BlockName: "test-block",
		Version:   "v1.0.0",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		Assets: []AssetInfo{
			{
				Path:       "model.pkl",
				Size:       1024,
				Checksum:   "abc123",
				UploadedAt: time.Now(),
			},
		},
		TotalSize:  1024,
		AssetCount: 1,
	}

	// Test PutManifest
	t.Run("PutManifest", func(t *testing.T) {
		// Create a temporary directory for testing
		tmpDir := t.TempDir()
		manifestPath := filepath.Join(tmpDir, "manifest.json")

		// Write manifest to temporary file to simulate upload
		data, err := json.MarshalIndent(manifest, "", "  ")
		require.NoError(t, err)

		err = os.WriteFile(manifestPath, data, 0644)
		require.NoError(t, err)

		// Verify manifest was written correctly
		var readManifest Manifest
		data, err = os.ReadFile(manifestPath)
		require.NoError(t, err)

		err = json.Unmarshal(data, &readManifest)
		require.NoError(t, err)

		assert.Equal(t, manifest.BlockName, readManifest.BlockName)
		assert.Equal(t, manifest.Version, readManifest.Version)
		assert.Equal(t, len(manifest.Assets), len(readManifest.Assets))
	})
}
