package cmd

import (
	"context"
	"fmt"
	"os"
	"path"
	"path/filepath"
	"strings"

	"github.com/example/clay/pkg/storage"
	"github.com/spf13/cobra"
)

var (
	storageURL string
	outputPath string
	parseSpec  string
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

If --parse is provided, <path> must be a directory and --parse names a
template file inside that directory. The template is rendered through Go's
text/template engine before uploading the directory. Use
{{ addUrl "file" }} inside the template to resolve relative asset
references against --url.`,
		Example: `  # Upload a plain directory or file
  clay block assets upload ./weights \
    --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1/

  # Parse a template file inside the directory and upload the directory
  clay block assets upload catalog_readme/ \
    --parse README.md:parsed.md \
    --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1/catalog_readme/

  # Parse with auto-generated output name
  # (README.md -> block-README.parsed.md)
  clay block assets upload docs/ \
    --parse README.md \
    --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1/docs/`,
		Args: cobra.ExactArgs(1),
		RunE: runBlockAssetsUpload,
	}

	cmd.Flags().StringVar(&storageURL, "url", "", "Storage URL where assets will be uploaded (required)")
	cmd.Flags().StringVar(&parseSpec, "parse", "",
		`Template file inside <path> to render before uploading
(format: <input>[:<output>]). Paths are relative to <path>.
Requires <path> to be a directory. Use {{ addUrl "file" }} to
resolve asset references against --url. Output defaults to
<name>.parsed<ext>.`)
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

	if parseSpec != "" {
		if !info.IsDir() {
			return fmt.Errorf("--parse requires <path> to be a directory containing the template; got file %q", localPath)
		}
		inputPath, parsedPath, err := resolveParseSpec(parseSpec, localPath)
		if err != nil {
			return err
		}
		fmt.Fprintf(os.Stderr, "Parsing template %s → %s...\n", inputPath, parsedPath)
		if err := parseTemplateFile(inputPath, parsedPath, storageURL); err != nil {
			return fmt.Errorf("failed to parse template: %w", err)
		}
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