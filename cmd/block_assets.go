package cmd

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/example/clay/api/marketplace"
	"github.com/example/clay/pkg/config"
	"github.com/example/clay/pkg/storage"
	"github.com/spf13/cobra"
)

var (
	assetBlockName    string
	assetBlockVersion string
	storageProvider   string
	storageBucket     string
	storageRegion     string
	outputPath        string
	isReadme          bool
)

// BlockAssetsCmd returns the assets command group
func BlockAssetsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "assets",
		Short: "Manage block assets in cloud storage",
		Long: `Manage assets associated with blocks in cloud storage.

Supports uploading, listing, and downloading files linked to a specific
block and version. Currently supports S3, with GCS and Azure planned.`,
		Example: `  # Upload a directory to S3
  clay block assets upload ./data -n my-block --bucket my-bucket --region us-east-1

  # List all assets for a block
  clay block assets list -n my-block --bucket my-bucket

  # Download a specific asset
  clay block assets download model.bin -n my-block --bucket my-bucket -o ./models/`,
	}

	// Block identification. Both name and version are optional; when omitted
	// they are read from clay.yaml in the current working directory.
	cmd.PersistentFlags().StringVarP(&assetBlockName, "name", "n", "", "Block name (default: read from clay.yaml)")
	cmd.PersistentFlags().StringVarP(&assetBlockVersion, "version", "v", "", "Block version (default: read from clay.yaml)")

	// Storage configuration
	cmd.PersistentFlags().StringVar(&storageProvider, "provider", "s3", "Storage provider: s3, gcs, azure")
	cmd.PersistentFlags().StringVar(&storageBucket, "bucket", "", "Storage bucket name")
	cmd.PersistentFlags().StringVar(&storageRegion, "region", "", "Storage region (optional for S3)")

	// Processing options
	// TODO: remove --readme once marketplace consumers migrate to publishing
	// pre-rendered docs directly. This flag exists to preserve the legacy
	// markdown template-processing flow (docs/README.md -> docs/parsed.md).
	cmd.PersistentFlags().BoolVar(&isReadme, "readme", false, "Process markdown templates before upload")

	cmd.MarkPersistentFlagRequired("bucket")

	cmd.AddCommand(blockAssetsUploadCmd())
	cmd.AddCommand(blockAssetsListCmd())
	cmd.AddCommand(blockAssetsDownloadCmd())

	return cmd
}

func blockAssetsUploadCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "upload <path>",
		Short: "Upload a file or directory to block storage",
		Long: `Upload a file or directory to cloud storage for a specific block.

When --readme is set, markdown templates are processed before upload
and the version is read from clay.yaml if not explicitly provided.`,
		Example: `  clay block assets upload ./data -n my-block --bucket my-bucket --region us-east-1
  clay block assets upload ./docs -n my-block --bucket my-bucket --readme`,
		Args: cobra.ExactArgs(1),
		RunE: runBlockAssetsUpload,
	}
}

func blockAssetsListCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "List all assets for a block",
		Long:  "List all assets stored for a specific block. Optionally filter by version.",
		Example: `  clay block assets list -n my-block --bucket my-bucket
  clay block assets list -n my-block -v 1.0.0 --bucket my-bucket`,
		RunE: runBlockAssetsList,
	}
}

func blockAssetsDownloadCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "download <asset-path>",
		Short: "Download an asset to the local filesystem",
		Long: `Download an asset from block storage to a local path.

If the asset is not found at the specified version, it falls back
to searching at the block (name) level.`,
		Example: `  clay block assets download model.bin -n my-block --bucket my-bucket
  clay block assets download model.bin -n my-block --bucket my-bucket -o ./models/`,
		Args: cobra.ExactArgs(1),
		RunE: runBlockAssetsDownload,
	}

	cmd.Flags().StringVarP(&outputPath, "output", "o", ".", "Local path to save the downloaded asset")
	return cmd
}

func runBlockAssetsUpload(cmd *cobra.Command, args []string) error {
	localPath := args[0]
	ctx := context.Background()

	if err := populateBlockIdentityFromConfig(); err != nil {
		return err
	}

	if _, err := os.Stat(localPath); err != nil {
		return fmt.Errorf("local path does not exist: %s", localPath)
	}

	// If readme flag is set, process markdown templates
	if isReadme {
		bucketURL := fmt.Sprintf("https://%s.s3.%s.amazonaws.com/", storageBucket, storageRegion)
		if storageRegion == "" {
			bucketURL = fmt.Sprintf("https://%s.s3.amazonaws.com/", storageBucket)
		}

		// Parse markdown using existing marketplace function
		fmt.Fprintln(os.Stderr, "Processing markdown templates...")
		err := marketplace.ParseMarkdown(assetBlockName, assetBlockVersion, bucketURL)
		if err != nil {
			return fmt.Errorf("failed to parse markdown: %w", err)
		}

		// Update localPath to the processed docs folder
		localPath = "docs"

		if _, err := os.Stat(localPath); err != nil {
			return fmt.Errorf("processed docs path does not exist: %s", localPath)
		}
	}

	// Create storage provider
	provider, err := createStorageProvider()
	if err != nil {
		return err
	}

	// Construct remote base path. When --readme is set we preserve the
	// "docs/" prefix on the remote key so that URLs rendered by
	// api/marketplace/catalog.go (which point to .../<block>/<version>/docs/<file>)
	// match the actual uploaded object keys.
	remotePath := getAssetPath(assetBlockName, assetBlockVersion)
	if isReadme {
		remotePath = fmt.Sprintf("%s/docs", remotePath)
	}

	// Check if uploading a directory or file
	fileInfo, err := os.Stat(localPath)
	if err != nil {
		return err
	}

	var uploadedURL string
	if fileInfo.IsDir() {
		fmt.Fprintf(os.Stderr, "Uploading directory %s to %s...\n", localPath, remotePath)
		err = provider.UploadDirectory(ctx, localPath, remotePath)
		if err == nil {
			uploadedURL = getPublicURL(remotePath)
		}
	} else {
		// For single file, append filename to remote path
		filename := filepath.Base(localPath)
		fullRemotePath := fmt.Sprintf("%s/%s", remotePath, filename)
		fmt.Fprintf(os.Stderr, "Uploading file %s to %s...\n", localPath, fullRemotePath)
		err = provider.Upload(ctx, localPath, fullRemotePath)
		if err == nil {
			uploadedURL = getPublicURL(fullRemotePath)
		}
	}

	if err != nil {
		return fmt.Errorf("upload failed: %w", err)
	}

	// Print success message to stderr (for humans)
	fmt.Fprintln(os.Stderr, "✓ Upload completed successfully")

	// Print URL to stdout (for scripts/CI)
	fmt.Println(uploadedURL)

	return nil
}

func runBlockAssetsList(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	if err := populateBlockIdentityFromConfig(); err != nil {
		return err
	}

	// Create storage provider
	provider, err := createStorageProvider()
	if err != nil {
		return err
	}

	// List assets
	assetPath := getAssetPath(assetBlockName, assetBlockVersion)
	fmt.Fprintf(os.Stderr, "Listing assets in %s...\n\n", assetPath)

	objects, err := provider.List(ctx, assetPath)
	if err != nil {
		return fmt.Errorf("failed to list assets: %w", err)
	}

	if len(objects) == 0 {
		fmt.Fprintln(os.Stderr, "No assets found")
		return nil
	}

	// Display assets
	for _, obj := range objects {
		// Show relative path from asset base
		relPath := strings.TrimPrefix(obj, assetPath+"/")
		if relPath != "" && relPath != obj {
			fmt.Fprintf(os.Stderr, "  %s\n", relPath)
		}
	}

	fmt.Fprintf(os.Stderr, "\nTotal: %d assets\n", len(objects))
	return nil
}

func runBlockAssetsDownload(cmd *cobra.Command, args []string) error {
	assetPath := args[0]
	ctx := context.Background()

	if err := populateBlockIdentityFromConfig(); err != nil {
		return err
	}

	// Create storage provider
	provider, err := createStorageProvider()
	if err != nil {
		return err
	}

	// Construct full remote path
	remotePath := fmt.Sprintf("%s/%s", getAssetPath(assetBlockName, assetBlockVersion), assetPath)

	// Determine local path
	var localPath string
	if outputPath == "." {
		// Use asset filename in current directory
		localPath = filepath.Base(assetPath)
	} else {
		// Check if output is a directory
		if info, err := os.Stat(outputPath); err == nil && info.IsDir() {
			localPath = filepath.Join(outputPath, filepath.Base(assetPath))
		} else {
			localPath = outputPath
		}
	}

	// Check if remote asset exists
	exists, err := provider.Exists(ctx, remotePath)
	if err != nil {
		return fmt.Errorf("failed to check asset existence: %w", err)
	}

	if !exists {
		// If version was specified, try name-level assets as fallback
		if assetBlockVersion != "" {
			nameOnlyPath := fmt.Sprintf("%s/%s", getAssetPath(assetBlockName, ""), assetPath)
			exists, err = provider.Exists(ctx, nameOnlyPath)
			if err != nil {
				return fmt.Errorf("failed to check name-level asset: %w", err)
			}
			if exists {
				remotePath = nameOnlyPath
				fmt.Fprintln(os.Stderr, "Asset not found at version level, downloading from name level...")
			} else {
				return fmt.Errorf("asset not found: %s", assetPath)
			}
		} else {
			return fmt.Errorf("asset not found: %s", assetPath)
		}
	}

	fmt.Fprintf(os.Stderr, "Downloading %s to %s...\n", assetPath, localPath)

	if err := provider.Download(ctx, remotePath, localPath); err != nil {
		return fmt.Errorf("download failed: %w", err)
	}

	fmt.Fprintln(os.Stderr, "✓ Download completed successfully")
	return nil
}

func createStorageProvider() (storage.Provider, error) {
	switch strings.ToLower(storageProvider) {
	case "s3":
		if storageBucket == "" {
			return nil, fmt.Errorf("bucket is required for S3 provider")
		}
		config := storage.S3Config{
			Region: storageRegion,
			Bucket: storageBucket,
		}
		return storage.NewS3Provider(config)

	case "gcs":
		return nil, fmt.Errorf("GCS provider not yet implemented")

	case "azure":
		return nil, fmt.Errorf("Azure provider not yet implemented")

	default:
		return nil, fmt.Errorf("unsupported storage provider: %s", storageProvider)
	}
}

func getAssetPath(blockName, version string) string {
	if version == "" {
		// Name-level assets (when version is not provided)
		return blockName
	}
	// Version-specific assets (when version is provided or loaded from config)
	return fmt.Sprintf("%s/%s", blockName, version)
}

func getPublicURL(remotePath string) string {
	switch strings.ToLower(storageProvider) {
	case "s3":
		if storageRegion == "" {
			return fmt.Sprintf("https://%s.s3.amazonaws.com/%s", storageBucket, remotePath)
		}
		return fmt.Sprintf("https://%s.s3.%s.amazonaws.com/%s", storageBucket, storageRegion, remotePath)
	case "gcs":
		return fmt.Sprintf("https://storage.googleapis.com/%s/%s", storageBucket, remotePath)
	case "azure":
		return fmt.Sprintf("https://%s.blob.core.windows.net/%s", storageBucket, remotePath)
	default:
		return ""
	}
}

// populateBlockIdentityFromConfig fills in assetBlockName and/or
// assetBlockVersion from clay.yaml in the current working directory when they
// are not provided via command-line flags. Returns an error if the config
// cannot be read and either field is still missing afterward.
func populateBlockIdentityFromConfig() error {
	if assetBlockName != "" && assetBlockVersion != "" {
		return nil
	}

	cwd, err := os.Getwd()
	if err != nil {
		return fmt.Errorf("failed to get current working directory: %w", err)
	}

	cfg, err := config.GetConfig(cwd)
	if err != nil {
		return fmt.Errorf("--name/--version not set and failed to read clay.yaml: %w", err)
	}

	if assetBlockName == "" {
		assetBlockName = cfg.Name
		fmt.Fprintf(os.Stderr, "Using block name from config: %s\n", assetBlockName)
	}
	if assetBlockVersion == "" {
		assetBlockVersion = cfg.Version
		fmt.Fprintf(os.Stderr, "Using version from config: %s\n", assetBlockVersion)
	}

	if assetBlockName == "" {
		return fmt.Errorf("block name is required: provide --name or set it in clay.yaml")
	}
	return nil
}
