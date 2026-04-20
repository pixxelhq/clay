package marketplace

import (
	"errors"
	"fmt"
	"html/template"
	"log"
	"net/url"
	"os"
	"path"
	"path/filepath"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
)

const catalogPath = "docs/README.md"

func UrlFuncMap(targetUrl string) map[string]interface{} {
	return map[string]interface{}{
		"addUrl": func(s string) string {
			return targetUrl + "/docs/" + s
		},
	}
}

func ParseMarkdown(blockName string, blockVersion string, s3BucketUrl string) error {
	targetUrl, err := url.Parse(s3BucketUrl)
	if err != nil {
		return fmt.Errorf("failed to parse bucket url: %w", err)
	}
	targetUrl.Path = path.Join(targetUrl.Path, blockName, blockVersion)

	if _, err := os.Stat(catalogPath); err != nil {
		return fmt.Errorf("expected %s to exist in the current directory: %w", catalogPath, err)
	}

	// Ensure the docs/ output directory exists before writing parsed.md. The
	// source README lives there too, but we guard against odd setups where
	// docs/ is a symlink or partially populated.
	if err := os.MkdirAll("docs", 0o755); err != nil {
		return fmt.Errorf("failed to create docs directory: %w", err)
	}

	temp := template.Must(template.New("README.md").Funcs(UrlFuncMap(targetUrl.String())).ParseFiles(catalogPath))
	fo, err := os.Create("docs/parsed.md")
	if err != nil {
		return err
	}
	defer fo.Close()
	if err := temp.Execute(fo, nil); err != nil {
		return fmt.Errorf("failed to render markdown template: %w", err)
	}
	return nil
}

func UploadDirectory(sess *session.Session, bucket, localFolderName, s3Namespace string) error {
	var filenames []string
	files, err := os.ReadDir(localFolderName)
	if err != nil {
		log.Fatal(err)
	}

	s3Client := s3.New(sess)

	for _, file := range files {
		if file.IsDir() {
			return errors.New("expected files, found directory")
		}
		filenames = append(filenames, file.Name())
	}

	for _, filename := range filenames {
		fileKey := filepath.Join(s3Namespace, filename)          // Key (object name) in S3
		fileToUpload := filepath.Join(localFolderName, filename) // Path to the file on your local system

		// Open the file
		file, err := os.Open(fileToUpload)
		if err != nil {
			panic(err)
		}
		defer file.Close()

		// Upload the file to S3 with the folder prefix
		_, err = s3Client.PutObject(&s3.PutObjectInput{
			Bucket: aws.String(bucket),
			Key:    aws.String(fileKey),
			Body:   file,
		})
		if err != nil {
			fmt.Printf("error while uploading file %s to s3", fileToUpload)
			panic(err)
		}
	}

	return nil
}
