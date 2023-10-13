package marketplace

import (
	"fmt"
	"path/filepath"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/example/clay/api/marketplace"
	"github.com/example/clay/cmd/common"
	"github.com/example/clay/pkg"
	"github.com/spf13/cobra"
)

const bucket = "d-platform-orchestrator-public-catalog-s3-01"

func UploadReadme() *cobra.Command {

	var (
		blockVersion string
		blockName    string
		err          error
	)

	cmd := &cobra.Command{
		Use:   "readme",
		Short: "Upload the readme for the model to cloud",
		PreRunE: func(cmd *cobra.Command, args []string) error {
			blockVersion, err = cmd.Flags().GetString("version")
			if err != nil {
				return err
			}

			if blockVersion != "" && !common.IsValidVersion(blockVersion) {
				return pkg.ErrInvalidValue("invalid version syntax. Follow semVer pattern eg. v0.0.1")
			}

			blockName, err = cmd.Flags().GetString("name")
			if err != nil {
				return err
			}

			return nil
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			logger := common.Getlogger()
			err := marketplace.ParseMarkdown(blockName, blockVersion)
			if err != nil {
				logger.Error().Err(err).Stack().Msg(err.Error())
				return err
			}

			fmt.Println("File parsed successfully, uploading...")
			awsSession, err := session.NewSession(&aws.Config{Region: aws.String("us-east-2")})
			if err != nil {
				return err
			}

			localReadmeFolder := "catalog_readme/"
			s3Namespace := filepath.Join(blockName, blockVersion, localReadmeFolder)
			versionedModelName := filepath.Join(blockName, blockVersion)
			err = marketplace.UploadDirectory(awsSession, bucket, localReadmeFolder, s3Namespace)
			if err != nil {
				logger.Error().Err(err).Stack().Msg(err.Error())
				return err
			}
			s3CatalogUrl := "https://d-platform-orchestrator-public-catalog-s3-01.s3.us-east-2.amazonaws.com/" + versionedModelName + "/catalog_readme/parsed.md"
			logger.Info().Msgf("catalog_content_url is: %s", string(s3CatalogUrl))

			return nil
		},
	}
	cmd.Flags().StringVarP(&blockName, "name", "n", "", "Name of block as specified in spec file")
	cmd.Flags().StringVarP(&blockVersion, "version", "v", "", "Version of block")
	cmd.MarkFlagRequired("name")
	cmd.MarkFlagRequired("version")
	return cmd
}
