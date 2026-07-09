package cmd

import (
	"context"
	"fmt"
	"net/url"
	"os"
	"path"
	"path/filepath"
	"strings"

	"github.com/pixxelhq/clay-framework/pkg/catalog"
	"github.com/pixxelhq/clay-framework/pkg/storage"
	"github.com/spf13/cobra"
)

var (
	storageURL string
	outputPath string
)

// BlockAssetsCmd returns the assets command group
func BlockAssetsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "assets",
		Short: "Manage block assets in cloud storage",
		Long: `Upload, list, and download assets associated with blocks in cloud storage.

Currently only AWS S3 is supported. Storage targets are identified by an
HTTPS URL of the form:

  https://<bucket>.s3.<region>.amazonaws.com/<prefix>

AWS credentials are read from the standard AWS SDK chain: environment
variables (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY), AWS_PROFILE,
shared config in ~/.aws/config (including SSO profiles), and IAM instance
roles.`,
	}

	cmd.AddCommand(blockAssetsUploadCmd())
	cmd.AddCommand(blockAssetsUploadCatalogCmd())
	cmd.AddCommand(blockAssetsListCmd())
	cmd.AddCommand(blockAssetsDownloadCmd())

	return cmd
}

func blockAssetsUploadCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "upload <path>",
		Short: "Upload a file or directory to block storage",
		Long: `Upload a file or directory verbatim to the storage location specified
by --url.

To publish a model's catalog.yaml media instead, use
'clay block assets upload-catalog'.`,
		Example: `  clay block assets upload ./weights \
    --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1/`,
		Args: cobra.ExactArgs(1),
		RunE: runBlockAssetsUpload,
	}

	cmd.Flags().StringVar(&storageURL, "url", "", "Storage URL where assets will be uploaded (required)")
	cmd.MarkFlagRequired("url")

	return cmd
}

func blockAssetsUploadCatalogCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "upload-catalog",
		Short: "Upload catalog.yaml media and rewrite it in place",
		Long: `Publish the media declared in a model repo's catalog.yaml.

Each file listed in the catalog's media: section is uploaded to
--url/<relPath> and its media: value is rewritten to the uploaded URL,
writing the result back to catalog.yaml in place. Entries that are already
uploaded URLs are skipped, so re-running is idempotent.

The catalog.yaml is read from the current working directory; the command
errors if none is found there. Bake the block/version into --url; the media
relative path is appended to it.`,
		Example: `  clay block assets upload-catalog \
    --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1/`,
		Args: cobra.NoArgs,
		RunE: runBlockAssetsUploadCatalog,
	}

	cmd.Flags().StringVar(&storageURL, "url", "", "Storage URL where media will be uploaded (required)")
	cmd.MarkFlagRequired("url")

	return cmd
}

func blockAssetsListCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List assets at a storage URL",
		Long:  "List all block assets stored at the location specified by --url.",
		Example: `  clay block assets list \
    --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1/`,
		RunE: runBlockAssetsList,
	}

	cmd.Flags().StringVar(&storageURL, "url", "", "Storage URL to list (required)")
	cmd.MarkFlagRequired("url")

	return cmd
}

func blockAssetsDownloadCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "download",
		Short: "Download a specific asset",
		Long:  "Download the asset at --url to the local filesystem.",
		Example: `  # Download to the current directory (saves as file.ext)
  clay block assets download \
    --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1/file.ext

  # Download to a specific path
  clay block assets download \
    --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1/file.ext \
    -o /tmp/file.ext`,
		Args: cobra.NoArgs,
		RunE: runBlockAssetsDownload,
	}

	cmd.Flags().StringVar(&storageURL, "url", "", "Complete storage URL of the asset to download (required)")
	cmd.Flags().StringVarP(&outputPath, "output", "o", ".", "Local path to save the downloaded asset (directory or filename)")
	cmd.MarkFlagRequired("url")

	return cmd
}

func runBlockAssetsUpload(cmd *cobra.Command, args []string) error {
	localPath := args[0]
	ctx := context.Background()

	info, err := os.Stat(localPath)
	if err != nil {
		return fmt.Errorf("local path does not exist: %s", localPath)
	}

	provider, remotePrefix, err := storage.ProviderFromURL(storageURL)
	if err != nil {
		return err
	}

	if info.IsDir() {
		fmt.Fprintf(os.Stderr, "Uploading directory %s to %s...\n", localPath, storageURL)
		if err := provider.UploadDirectory(ctx, localPath, remotePrefix); err != nil {
			return fmt.Errorf("upload failed: %w", err)
		}
	} else {
		filename := filepath.Base(localPath)
		fullRemote := path.Join(remotePrefix, filename)
		fmt.Fprintf(os.Stderr, "Uploading file %s to %s/%s...\n", localPath, strings.TrimRight(storageURL, "/"), filename)
		if err := provider.Upload(ctx, localPath, fullRemote); err != nil {
			return fmt.Errorf("upload failed: %w", err)
		}
	}

	fmt.Fprintln(os.Stderr, "✓ Upload completed successfully")
	fmt.Println(storageURL)
	return nil
}

func runBlockAssetsList(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	provider, remotePrefix, err := storage.ProviderFromURL(storageURL)
	if err != nil {
		return err
	}

	fmt.Fprintf(os.Stderr, "Listing assets at %s...\n\n", storageURL)

	objects, err := provider.List(ctx, remotePrefix)
	if err != nil {
		return fmt.Errorf("failed to list assets: %w", err)
	}

	if len(objects) == 0 {
		fmt.Fprintln(os.Stderr, "No assets found")
		return nil
	}

	for _, obj := range objects {
		relPath := strings.TrimPrefix(obj, strings.TrimSuffix(remotePrefix, "/")+"/")
		if relPath == "" {
			continue
		}
		fmt.Fprintf(os.Stderr, "  %s\n", relPath)
	}

	fmt.Fprintf(os.Stderr, "\nTotal: %d assets\n", len(objects))
	return nil
}

func runBlockAssetsDownload(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	provider, remotePath, err := storage.ProviderFromURL(storageURL)
	if err != nil {
		return err
	}

	if remotePath == "" || strings.HasSuffix(remotePath, "/") {
		return fmt.Errorf("--url %q does not point at a file; include the filename in the URL (e.g. https://bucket.s3.region.amazonaws.com/prefix/file.ext)", storageURL)
	}
	remoteBase := path.Base(remotePath)
	if remoteBase == "." || remoteBase == "/" {
		return fmt.Errorf("--url %q does not point at a file; include the filename in the URL (e.g. https://bucket.s3.region.amazonaws.com/prefix/file.ext)", storageURL)
	}

	var localPath string
	if outputPath == "." {
		localPath = remoteBase
	} else if info, err := os.Stat(outputPath); err == nil && info.IsDir() {
		localPath = filepath.Join(outputPath, remoteBase)
	} else {
		localPath = outputPath
	}

	exists, err := provider.Exists(ctx, remotePath)
	if err != nil {
		return fmt.Errorf("failed to check asset existence: %w", err)
	}
	if !exists {
		return fmt.Errorf("asset not found: %s", storageURL)
	}

	fmt.Fprintf(os.Stderr, "Downloading %s to %s...\n", storageURL, localPath)

	if err := provider.Download(ctx, remotePath, localPath); err != nil {
		return fmt.Errorf("download failed: %w", err)
	}

	fmt.Fprintln(os.Stderr, "✓ Download completed successfully")
	return nil
}

func runBlockAssetsUploadCatalog(cmd *cobra.Command, args []string) error {
	repoDir, err := os.Getwd()
	if err != nil {
		return err
	}
	ctx := context.Background()

	provider, remotePrefix, err := storage.ProviderFromURL(storageURL)
	if err != nil {
		return err
	}

	return uploadCatalog(ctx, provider, remotePrefix, repoDir)
}

type mediaUpload struct {
	key     string
	relPath string
	absPath string
}

// uploadCatalog uploads every local file declared in the catalog's media:
// section to --url/<relPath>, rewrites those media: values to the uploaded URLs
// in place, and finally uploads the rewritten catalog.yaml itself so the
// published catalog lives alongside the media it references.
func uploadCatalog(ctx context.Context, provider storage.Provider, remotePrefix, repoDir string) error {
	catalogPath := catalog.FilePath(repoDir)
	cat, err := loadCatalog(catalogPath)
	if err != nil {
		return err
	}
	if len(cat.Media) == 0 {
		return fmt.Errorf("%s has no media: section, nothing to upload", catalogPath)
	}
	pending, err := mediaToUpload(cat, repoDir)
	if err != nil {
		return err
	}

	if len(pending) > 0 {
		if err := uploadMedia(ctx, provider, remotePrefix, cat, pending); err != nil {
			return err
		}
		if err := cat.WriteFile(catalogPath); err != nil {
			return err
		}
		fmt.Fprintf(os.Stderr, "✓ Uploaded %d media file(s); wrote rewritten catalog to %s\n", len(pending), catalogPath)
	} else {
		fmt.Fprintln(os.Stderr, "✓ All catalog media are already uploaded URLs")
	}

	// Upload catalog.yaml itself alongside its media.
	if err := uploadCatalogFile(ctx, provider, remotePrefix, catalogPath); err != nil {
		return err
	}

	fmt.Println(storageURL)
	return nil
}

func loadCatalog(catalogPath string) (*catalog.Catalog, error) {
	cat, err := catalog.LoadFile(catalogPath)
	if err != nil {
		return nil, err
	}
	if cat == nil {
		return nil, fmt.Errorf("catalog file not found: %s", catalogPath)
	}
	return cat, nil
}

// mediaToUpload returns the media entries that still point to local files.
// Entries already rewritten to remote URLs are skipped.
func mediaToUpload(cat *catalog.Catalog, repoDir string) ([]mediaUpload, error) {
	pending := make([]mediaUpload, 0, len(cat.Media))
	for key, val := range cat.Media {
		if catalog.IsRemoteURL(val) {
			fmt.Fprintf(os.Stderr, "Skipping catalog media %q: already an uploaded URL\n", key)
			continue
		}
		abs, err := catalog.ResolvePath(repoDir, val)
		if err != nil {
			return nil, fmt.Errorf("catalog media %q: %w", key, err)
		}
		pending = append(pending, mediaUpload{
			key:     key,
			relPath: filepath.ToSlash(filepath.Clean(val)),
			absPath: abs,
		})
	}
	return pending, nil
}

// uploadMedia uploads each pending file and rewrites its catalog entry to the
// resulting remote URL.
func uploadMedia(ctx context.Context, provider storage.Provider, remotePrefix string, cat *catalog.Catalog, pending []mediaUpload) error {
	for _, m := range pending {
		remoteURL, err := uploadFile(ctx, provider, remotePrefix, m.absPath, m.relPath, fmt.Sprintf("catalog media %q", m.key))
		if err != nil {
			return err
		}
		cat.Media[m.key] = remoteURL
	}
	return nil
}

// uploadCatalogFile uploads the catalog.yaml itself to remotePrefix/<filename>,
// keeping it under the same prefix as the media it references.
func uploadCatalogFile(ctx context.Context, provider storage.Provider, remotePrefix, catalogPath string) error {
	filename := filepath.Base(catalogPath)
	_, err := uploadFile(ctx, provider, remotePrefix, catalogPath, filename, filename)
	return err
}

// uploadFile uploads localPath to remotePrefix/relPath and returns the public
// URL it was published to. label names the item in progress output and errors.
func uploadFile(ctx context.Context, provider storage.Provider, remotePrefix, localPath, relPath, label string) (string, error) {
	remoteURL, err := url.JoinPath(storageURL, relPath)
	if err != nil {
		return "", fmt.Errorf("%s: %w", label, err)
	}
	fmt.Fprintf(os.Stderr, "Uploading %s → %s...\n", label, remoteURL)
	if err := provider.Upload(ctx, localPath, path.Join(remotePrefix, relPath)); err != nil {
		return "", fmt.Errorf("failed to upload %s: %w", label, err)
	}
	return remoteURL, nil
}
