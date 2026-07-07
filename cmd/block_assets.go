package cmd

import (
	"context"
	"fmt"
	"os"
	"path"
	"path/filepath"
	"sort"
	"strings"

	"github.com/pixxelhq/clay-framework/pkg/catalog"
	"github.com/pixxelhq/clay-framework/pkg/storage"
	"github.com/spf13/cobra"
)

var (
	storageURL  string
	outputPath  string
	catalogFile string
	catalogOut  string
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
	cmd.AddCommand(blockAssetsListCmd())
	cmd.AddCommand(blockAssetsDownloadCmd())

	return cmd
}

func blockAssetsUploadCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "upload <path>",
		Short: "Upload assets to block storage",
		Long: `Upload a file or directory to the storage location specified by --url.

If --catalog is provided, <path> must be the model repo directory and
--catalog names a catalog.yaml inside it: each file declared in its media:
section is uploaded and the media: values are rewritten to the uploaded URLs.`,
		Example: `  # Upload a plain directory or file
  clay block assets upload ./weights \
    --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1/

  # Upload the media declared in catalog.yaml and rewrite it in place.
  # Bake the block/version into --url.
  clay block assets upload . \
    --catalog catalog.yaml \
    --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1/`,
		Args: cobra.ExactArgs(1),
		RunE: runBlockAssetsUpload,
	}

	cmd.Flags().StringVar(&storageURL, "url", "", "Storage URL where assets will be uploaded (required)")
	cmd.Flags().StringVar(&catalogFile, "catalog", "",
		`Catalog filename inside <path> (e.g. catalog.yaml). Uploads
each file declared in its media: section to --url/<relPath>,
then rewrites those media: values to the uploaded URLs. Bake
the block/version into --url; the media relative path is
appended to it.`)
	cmd.Flags().StringVar(&catalogOut, "out", "",
		`Where to write the rewritten catalog (with --catalog).
Relative paths are resolved against <path>. Defaults to
overwriting the --catalog file in place.`)
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

	if catalogFile != "" {
		if !info.IsDir() {
			return fmt.Errorf("--catalog requires <path> to be the model repo directory; got file %q", localPath)
		}
		return runCatalogUpload(ctx, provider, remotePrefix, localPath)
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

func runCatalogUpload(ctx context.Context, provider storage.Provider, remotePrefix, repoDir string) error {
	catPath := filepath.Join(repoDir, catalogFile)
	cat, err := catalog.LoadFile(catPath)
	if err != nil {
		return err
	}
	if cat == nil {
		return fmt.Errorf("catalog file not found: %s", catPath)
	}

	if len(cat.Media) == 0 {
		return fmt.Errorf("%s has no media: section, nothing to upload", catPath)
	}

	keys := make([]string, 0, len(cat.Media))
	for key := range cat.Media {
		keys = append(keys, key)
	}
	sort.Strings(keys)

	abs := make(map[string]string, len(cat.Media))
	for _, key := range keys {
		p, err := catalog.ResolvePath(repoDir, cat.Media[key])
		if err != nil {
			return fmt.Errorf("media key %q: %w", key, err)
		}
		abs[key] = p
	}

	base := strings.TrimRight(storageURL, "/")
	for _, key := range keys {
		rel := cat.Media[key]
		fmt.Fprintf(os.Stderr, "Uploading catalog media %q → %s/%s...\n", key, base, rel)
		if err := provider.Upload(ctx, abs[key], path.Join(remotePrefix, rel)); err != nil {
			return fmt.Errorf("failed to upload catalog media %q: %w", key, err)
		}
		cat.Media[key] = base + "/" + rel
	}

	outPath := catPath
	if catalogOut != "" {
		outPath = catalogOut
		if !filepath.IsAbs(outPath) {
			outPath = filepath.Join(repoDir, outPath)
		}
	}
	out, err := cat.Bytes()
	if err != nil {
		return err
	}
	if err := os.WriteFile(outPath, out, 0644); err != nil {
		return fmt.Errorf("failed to write rewritten catalog: %w", err)
	}

	fmt.Fprintf(os.Stderr, "✓ Uploaded %d media file(s); wrote rewritten catalog to %s\n", len(cat.Media), outPath)
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
