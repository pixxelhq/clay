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

const (
	localReadmeFolder = "catalog_readme/"
	s3Bucket = "p-platform-clay-public-catalog-s3-01" //TODO: this should be removed before making clay opensource
)

var s3CatalogUrl string

func UploadReadme() *cobra.Command {

	var (
		blockVersion string
		blockName    string
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

			blockVersion, err = cmd.Flags().GetString("version")
			if err != nil || blockVersion == "" {
				blockVersion = cfg.Version
			}

			if blockVersion != "" && !common.IsValidVersion(blockVersion) {
				return pkg.ErrInvalidValue("invalid version syntax. Follow semVer pattern eg. v0.0.1")
			}

			blockName, err = cmd.Flags().GetString("name")
			if err != nil || blockName == "" {
				blockName = cfg.Name
			}

			return nil
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			logger := common.Getlogger()
			s3Namespace := filepath.Join(blockName, blockVersion, localReadmeFolder)
			versionedBlockName := filepath.Join(blockName, blockVersion)
			s3BucketUrl := "https://" + s3Bucket + ".s3.us-east-2.amazonaws.com/"
			err := marketplace.ParseMarkdown(blockName, blockVersion, s3BucketUrl)
			if err != nil {
				logger.Error().Err(err).Stack().Msg(err.Error())
				return err
			}
			awsSession, err := session.NewSession(&aws.Config{Region: aws.String("us-east-2")})
			if err != nil {
				return err
			}
			err = marketplace.UploadDirectory(awsSession, s3Bucket, localReadmeFolder, s3Namespace)
			if err != nil {
				logger.Error().Err(err).Stack().Msg(err.Error())
				return err
			}
			s3CatalogUrl = "https://" + s3Bucket + ".s3.us-east-2.amazonaws.com/" + versionedBlockName + "/catalog_readme/parsed.md"
			fmt.Print(string(s3CatalogUrl))
			return nil
		},
	}
	cmd.Flags().StringVarP(&blockName, "name", "n", "", "Name of block as specified in spec file")
	cmd.Flags().StringVarP(&blockVersion, "version", "v", "", "Version of block")
	return cmd
}

func GetS3CatalogUrl() (string, error) {
	if s3CatalogUrl == "" {
		return "", errors.New("catlog url is empty")
	}

	return s3CatalogUrl, nil
}
