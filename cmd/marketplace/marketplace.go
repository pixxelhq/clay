package marketplace

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/example/clay/api/marketplace"
	"github.com/example/clay/cmd/common"
	"github.com/example/clay/pkg"
	"github.com/example/clay/pkg/config"
	"github.com/spf13/cobra"
)

const localReadmeFolder = "docs/"

var s3CatalogUrl string

// UploadReadme is the legacy `clay upload readme` implementation. It is
// retained only to keep existing CI integrations (e.g. the Orchestrator
// orchestrator) working during the deprecation window. New users should use
// `clay block assets upload --readme` instead, which supports configurable
// providers/buckets cleanly.
//
// TODO: remove once all callers migrate off `clay upload readme`.
func UploadReadme() *cobra.Command {

	var (
		blockVersion string
		blockName    string
		s3Bucket     string
		s3Region     string
	)

	cmd := &cobra.Command{
		Use:   "readme",
		Short: "Upload the readme for the block to cloud",
		PreRunE: func(cmd *cobra.Command, args []string) error {
			cwd, err := os.Getwd()
			if err != nil {
				return err
			}

			cfg, err := config.GetConfig(cwd)
			if err != nil {
				return err
			}

			if blockVersion == "" {
				blockVersion = cfg.Version
			}

			if blockVersion != "" && !common.IsValidVersion(blockVersion) {
				return pkg.ErrInvalidValue("invalid version syntax. Follow semVer pattern eg. v0.0.1")
			}

			if blockName == "" {
				blockName = cfg.Name
			}

			if s3Bucket == "" {
				s3Bucket = os.Getenv("CLAY_CATALOG_S3_BUCKET")
			}
			if s3Region == "" {
				if v := os.Getenv("CLAY_CATALOG_S3_REGION"); v != "" {
					s3Region = v
				} else {
					s3Region = "us-east-2"
				}
			}
			if s3Bucket == "" {
				return pkg.ErrInvalidValue("--bucket is required (or set CLAY_CATALOG_S3_BUCKET)")
			}

			return nil
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			logger := common.Getlogger()
			s3Namespace := filepath.Join(blockName, blockVersion, localReadmeFolder)
			versionedBlockName := filepath.Join(blockName, blockVersion)
			s3BucketUrl := fmt.Sprintf("https://%s.s3.%s.amazonaws.com/", s3Bucket, s3Region)
			err := marketplace.ParseMarkdown(blockName, blockVersion, s3BucketUrl)
			if err != nil {
				logger.Error().Err(err).Stack().Msg(err.Error())
				return err
			}
			awsSession, err := session.NewSession(&aws.Config{Region: aws.String(s3Region)})
			if err != nil {
				return err
			}
			err = marketplace.UploadDirectory(awsSession, s3Bucket, localReadmeFolder, s3Namespace)
			if err != nil {
				logger.Error().Err(err).Stack().Msg(err.Error())
				return err
			}
			s3CatalogUrl = fmt.Sprintf("https://%s.s3.%s.amazonaws.com/%s/docs/parsed.md", s3Bucket, s3Region, versionedBlockName)
			fmt.Print(string(s3CatalogUrl))
			return nil
		},
	}
	cmd.Flags().StringVarP(&blockName, "name", "n", "", "Name of block as specified in spec file")
	cmd.Flags().StringVarP(&blockVersion, "version", "v", "", "Version of block")
	cmd.Flags().StringVar(&s3Bucket, "bucket", "", "S3 bucket to upload the readme to (or set CLAY_CATALOG_S3_BUCKET)")
	cmd.Flags().StringVar(&s3Region, "region", "", "S3 region (or set CLAY_CATALOG_S3_REGION, default us-east-2)")
	return cmd
}

func GetS3CatalogUrl() (string, error) {
	if s3CatalogUrl == "" {
		return "", errors.New("catalog url is empty")
	}

	return s3CatalogUrl, nil
}
