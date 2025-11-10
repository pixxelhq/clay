package storage

import (
	"context"
	"time"
)

// AssetInfo represents metadata about a single asset
type AssetInfo struct {
	Path        string    `json:"path"`
	Size        int64     `json:"size"`
	Checksum    string    `json:"checksum"`
	UploadedAt  time.Time `json:"uploaded_at"`
	UploadedBy  string    `json:"uploaded_by,omitempty"`
	ContentType string    `json:"content_type,omitempty"`
}

// Manifest represents a collection of assets with metadata
type Manifest struct {
	BlockName  string      `json:"block_name"`
	Version    string      `json:"version,omitempty"`
	CreatedAt  time.Time   `json:"created_at"`
	UpdatedAt  time.Time   `json:"updated_at"`
	Assets     []AssetInfo `json:"assets"`
	TotalSize  int64       `json:"total_size"`
	AssetCount int         `json:"asset_count"`
}

// Provider defines the interface for storage operations
type Provider interface {
	// Upload uploads a single file to the storage backend
	Upload(ctx context.Context, localPath, remotePath string) error

	// UploadDirectory uploads all files in a directory to the storage backend
	UploadDirectory(ctx context.Context, localDir, remotePrefix string) error

	// Download downloads a single file from the storage backend
	Download(ctx context.Context, remotePath, localPath string) error

	// List returns all objects under the given prefix
	List(ctx context.Context, prefix string) ([]string, error)

	// Exists checks if an object exists in the storage backend
	Exists(ctx context.Context, remotePath string) (bool, error)
}
