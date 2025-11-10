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
		Long:  "Upload, list, and download assets associated with blocks in cloud storage (S3, GCS, Azure)",
	}

	cmd.PersistentFlags().StringVarP(&assetBlockName, "name", "n", "", "Name of the block (required)")
	cmd.PersistentFlags().StringVarP(&assetBlockVersion, "version", "v", "", "Version of the block (optional, reads from config when --readme flag is set)")
	cmd.PersistentFlags().BoolVar(&isReadme, "readme", false, "Process markdown templates before upload (for catalog/README files)")
	cmd.MarkPersistentFlagRequired("name")

	cmd.AddCommand(blockAssetsUploadCmd())
	cmd.AddCommand(blockAssetsListCmd())
	cmd.AddCommand(blockAssetsDownloadCmd())

	return cmd
}

func blockAssetsUploadCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "upload <path>",
		Short: "Upload assets to block storage",
		Long:  "Upload a file or directory to cloud storage for a specific block",
		Args:  cobra.ExactArgs(1),
		RunE:  runBlockAssetsUpload,
	}

	cmd.Flags().StringVar(&storageProvider, "provider", "s3", "Storage provider (s3, gcs, azure)")
	cmd.Flags().StringVar(&storageBucket, "bucket", "", "Storage bucket name (required)")
	cmd.Flags().StringVar(&storageRegion, "region", "", "Storage region (required for S3)")
	cmd.MarkFlagRequired("bucket")

	return cmd
}

func blockAssetsListCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List assets for a block",
		Long:  "List all assets stored for a specific block and optionally version",
		RunE:  runBlockAssetsList,
	}

	cmd.Flags().StringVar(&storageProvider, "provider", "s3", "Storage provider (s3, gcs, azure)")
	cmd.Flags().StringVar(&storageBucket, "bucket", "", "Storage bucket name (required)")
	cmd.Flags().StringVar(&storageRegion, "region", "", "Storage region (required for S3)")
	cmd.MarkFlagRequired("bucket")

	return cmd
}

func blockAssetsDownloadCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "download <asset-path>",
		Short: "Download a specific asset",
		Long:  "Download an asset from block storage to local filesystem",
		Args:  cobra.ExactArgs(1),
		RunE:  runBlockAssetsDownload,
	}

	cmd.Flags().StringVar(&storageProvider, "provider", "s3", "Storage provider (s3, gcs, azure)")
	cmd.Flags().StringVar(&storageBucket, "bucket", "", "Storage bucket name (required)")
	cmd.Flags().StringVar(&storageRegion, "region", "", "Storage region (required for S3)")
	cmd.Flags().StringVarP(&outputPath, "output", "o", ".", "Local path to save the downloaded asset")
	cmd.MarkFlagRequired("bucket")

	return cmd
}

func runBlockAssetsUpload(cmd *cobra.Command, args []string) error {
	localPath := args[0]
	ctx := context.Background()

	if _, err := os.Stat(localPath); err != nil {
		return fmt.Errorf("local path does not exist: %s", localPath)
	}

	// If readme flag is set, process markdown templates
	if isReadme {
		// Load version from config if not provided (needed for markdown processing)
		if err := populateVersionFromConfig(); err != nil {
			return err
		}
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

		// Update localPath to the processed catalog_readme folder
		localPath = "catalog_readme"

		if _, err := os.Stat(localPath); err != nil {
			return fmt.Errorf("processed catalog path does not exist: %s", localPath)
		}
	}

	// Create storage provider
	provider, err := createStorageProvider()
	if err != nil {
		return err
	}

	// Construct remote base path
	remotePath := getAssetPath(assetBlockName, assetBlockVersion)

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

// populateVersionFromConfig reads the version from clay.yaml when it's not explicitly
// provided via command-line flags. This should only be called when version is needed
// (e.g., when --readme flag is set).
func populateVersionFromConfig() error {
	if assetBlockVersion == "" {
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("failed to get current working directory: %w", err)
		}

		cfg, err := config.GetConfig(cwd)
		if err != nil {
			return fmt.Errorf("failed to read config file: %w", err)
		}

		assetBlockVersion = cfg.Version
		fmt.Fprintf(os.Stderr, "Using version from config: %s\n", assetBlockVersion)
	}
	return nil
}
