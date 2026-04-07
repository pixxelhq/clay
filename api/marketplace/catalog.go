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

const catalogPath = "catalog_readme/block-README.md"

func UrlFuncMap(targetUrl string) map[string]interface{} {
	return map[string]interface{}{
		"addUrl": func(s string) string {
			return targetUrl + "/catalog_readme/" + s
		},
	}
}

func ParseMarkdown(blockName string, blockVersion string, s3BucketUrl string) error {

	targetUrl, err := url.Parse(s3BucketUrl)
	if err != nil {
		log.Fatal(err)
	}
	targetUrl.Path = path.Join(targetUrl.Path, blockName, blockVersion)

	temp := template.Must(template.New("block-README.md").Funcs(UrlFuncMap(targetUrl.String())).ParseFiles(catalogPath))
	fo, err := os.Create("catalog_readme/parsed.md")
	if err != nil {
		return err
	}
	defer fo.Close()
	err = temp.Execute(fo, nil)
	if err != nil {
		log.Fatal(err)
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
