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

const catalogPath = "catalog_readme/model-README.md"

const catalogBucketUrl = "https://d-platform-orchestrator-public-catalog-s3-01.s3.us-east-2.amazonaws.com/"

func UrlFuncMap(targetUrl string) map[string]interface{} {
	return map[string]interface{}{
		"addUrl": func(s string) string {
			return targetUrl + "/catalog_readme/" + s
		},
	}
}

func ParseMarkdown(blockName string, blockVersion string) error {

	targetUrl, err := url.Parse(catalogBucketUrl)
	if err != nil {
		log.Fatal(err)
	}
	targetUrl.Path = path.Join(targetUrl.Path, blockName, blockVersion)

	temp := template.Must(template.New("model-README.md").Funcs(UrlFuncMap(targetUrl.String())).ParseFiles(catalogPath))
	fo, err := os.Create("catalog_readme/parsed.md")
	if err != nil {
		return err
	}
	defer fo.Close()
	err = temp.Execute(fo, nil)
	if err != nil {
		log.Fatal(err)
	} else {
		fmt.Println("File parsed successfully, uploading...")
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

		fmt.Printf("uploaded %s to s3 in namespace: %s", fileToUpload, s3Namespace)

	}

	return nil
}
