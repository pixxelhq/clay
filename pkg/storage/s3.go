package storage

import (
	"context"
	"fmt"
	"io"
	"mime"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/request"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
)

// extContentTypes pins the Content-Type for extensions we care about, so the
// result does not depend on the host's mime.types registry (mp4 in particular
// is often absent). Checked before mime.TypeByExtension and magic-byte sniffing.
var extContentTypes = map[string]string{
	".png":  "image/png",
	".jpg":  "image/jpeg",
	".jpeg": "image/jpeg",
	".gif":  "image/gif",
	".webp": "image/webp",
	".svg":  "image/svg+xml",
	".mp4":  "video/mp4",
	".webm": "video/webm",
	".mov":  "video/quicktime",
	".pdf":  "application/pdf",
	".json": "application/json",
}

// detectContentType determines an object's Content-Type from its extension,
// falling back to magic-byte sniffing of the first 512 bytes. r is rewound to
// the start before returning so the caller can upload from the beginning.
func detectContentType(path string, r io.ReadSeeker) (string, error) {
	ext := strings.ToLower(filepath.Ext(path))
	if ct, ok := extContentTypes[ext]; ok {
		return ct, nil
	}
	if ct := mime.TypeByExtension(ext); ct != "" {
		return ct, nil
	}

	buf := make([]byte, 512)
	n, err := r.Read(buf)
	if err != nil && err != io.EOF {
		return "", fmt.Errorf("failed to read file for content-type detection: %w", err)
	}
	if _, err := r.Seek(0, io.SeekStart); err != nil {
		return "", fmt.Errorf("failed to rewind file after content-type detection: %w", err)
	}
	return http.DetectContentType(buf[:n]), nil
}

// S3Config holds S3-specific configuration
type S3Config struct {
	Region string
	Bucket string
}

// s3Client interface for testing
type s3Client interface {
	HeadObjectWithContext(ctx context.Context, input *s3.HeadObjectInput, opts ...request.Option) (*s3.HeadObjectOutput, error)
	DeleteObjectWithContext(ctx context.Context, input *s3.DeleteObjectInput, opts ...request.Option) (*s3.DeleteObjectOutput, error)
	ListObjectsV2PagesWithContext(ctx context.Context, input *s3.ListObjectsV2Input, fn func(*s3.ListObjectsV2Output, bool) bool, opts ...request.Option) error
}

// S3Provider implements Provider interface for AWS S3
type S3Provider struct {
	client     s3Client
	uploader   *s3manager.Uploader
	downloader *s3manager.Downloader
	bucket     string
}

// NewS3Provider creates a new S3 storage provider
func NewS3Provider(config S3Config) (*S3Provider, error) {
	awsConfig := &aws.Config{}
	if config.Region != "" {
		awsConfig.Region = aws.String(config.Region)
	}

	// SharedConfigEnable makes the SDK honor AWS_PROFILE / ~/.aws/config,
	// including SSO profiles (SDK v1 ignores these by default).
	sess, err := session.NewSessionWithOptions(session.Options{
		Config:            *awsConfig,
		SharedConfigState: session.SharedConfigEnable,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create AWS session: %w", err)
	}

	return &S3Provider{
		client:     s3.New(sess),
		uploader:   s3manager.NewUploader(sess),
		downloader: s3manager.NewDownloader(sess),
		bucket:     config.Bucket,
	}, nil
}

// Upload uploads a single file to S3
func (p *S3Provider) Upload(ctx context.Context, localPath, remotePath string) error {
	file, err := os.Open(localPath)
	if err != nil {
		return fmt.Errorf("failed to open file %s: %w", localPath, err)
	}
	defer file.Close()

	key := p.normalizeKey(remotePath)

	contentType, err := detectContentType(localPath, file)
	if err != nil {
		return err
	}

	_, err = p.uploader.UploadWithContext(ctx, &s3manager.UploadInput{
		Bucket:      aws.String(p.bucket),
		Key:         aws.String(key),
		Body:        file,
		ContentType: aws.String(contentType),
	})

	if err != nil {
		return fmt.Errorf("failed to upload file to S3: %w", err)
	}

	return nil
}

// UploadDirectory uploads all files in a directory to S3
func (p *S3Provider) UploadDirectory(ctx context.Context, localDir, remotePrefix string) error {
	return filepath.Walk(localDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			return nil
		}

		// Get relative path from localDir
		relPath, err := filepath.Rel(localDir, path)
		if err != nil {
			return fmt.Errorf("failed to get relative path: %w", err)
		}

		// Convert to forward slashes for S3
		relPath = filepath.ToSlash(relPath)
		remotePath := fmt.Sprintf("%s/%s", strings.TrimSuffix(remotePrefix, "/"), relPath)

		return p.Upload(ctx, path, remotePath)
	})
}

// Download downloads a single file from S3
func (p *S3Provider) Download(ctx context.Context, remotePath, localPath string) error {
	// Ensure local directory exists
	if err := os.MkdirAll(filepath.Dir(localPath), 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	file, err := os.Create(localPath)
	if err != nil {
		return fmt.Errorf("failed to create file %s: %w", localPath, err)
	}
	defer file.Close()

	key := p.normalizeKey(remotePath)

	_, err = p.downloader.DownloadWithContext(ctx, file, &s3.GetObjectInput{
		Bucket: aws.String(p.bucket),
		Key:    aws.String(key),
	})

	if err != nil {
		return fmt.Errorf("failed to download file from S3: %w", err)
	}

	return nil
}

// List returns all objects under the given prefix
func (p *S3Provider) List(ctx context.Context, prefix string) ([]string, error) {
	var objects []string

	prefix = p.normalizeKey(prefix)

	err := p.client.ListObjectsV2PagesWithContext(ctx, &s3.ListObjectsV2Input{
		Bucket: aws.String(p.bucket),
		Prefix: aws.String(prefix),
	}, func(page *s3.ListObjectsV2Output, lastPage bool) bool {
		for _, obj := range page.Contents {
			objects = append(objects, *obj.Key)
		}
		return true
	})

	if err != nil {
		return nil, fmt.Errorf("failed to list objects: %w", err)
	}

	return objects, nil
}

// Exists checks if an object exists in S3
func (p *S3Provider) Exists(ctx context.Context, remotePath string) (bool, error) {
	key := p.normalizeKey(remotePath)

	_, err := p.client.HeadObjectWithContext(ctx, &s3.HeadObjectInput{
		Bucket: aws.String(p.bucket),
		Key:    aws.String(key),
	})

	if err != nil {
		// Check if the error is because the object doesn't exist
		if strings.Contains(err.Error(), "NotFound") {
			return false, nil
		}
		return false, fmt.Errorf("failed to check object existence: %w", err)
	}

	return true, nil
}

// normalizeKey ensures the S3 key is properly formatted
func (p *S3Provider) normalizeKey(key string) string {
	// Remove s3:// prefix if present
	key = strings.TrimPrefix(key, "s3://")

	// Remove bucket name if present
	parts := strings.SplitN(key, "/", 2)
	if len(parts) > 1 && parts[0] == p.bucket {
		key = parts[1]
	}

	// Remove leading slash
	return strings.TrimPrefix(key, "/")
}
