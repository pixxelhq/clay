package storage

import (
	"fmt"
	"net/url"
	"regexp"
	"strings"
)

// s3HostPattern matches AWS S3 virtual-hosted HTTPS hostnames of the form:
//
//	<bucket>.s3.<region>.amazonaws.com
//
// The region is required — callers must encode it in the URL so the SDK
// never has to go look it up at runtime.
var s3HostPattern = regexp.MustCompile(`^(?P<bucket>[^.]+)\.s3\.(?P<region>[^.]+)\.amazonaws\.com$`)

// ProviderFromURL parses a complete storage URL and returns a configured
// Provider along with the remote key path extracted from the URL.
//
// Supported form:
//
//	https://<bucket>.s3.<region>.amazonaws.com/<prefix>
//
// s3:// URIs and other schemes are explicitly unsupported. To add another
// backend, add a case to the switch below.
func ProviderFromURL(rawURL string) (Provider, string, error) {
	u, err := url.Parse(rawURL)
	if err != nil {
		return nil, "", fmt.Errorf("invalid storage URL %q: %w", rawURL, err)
	}

	switch strings.ToLower(u.Scheme) {
	case "https":
		if u.RawQuery != "" {
			return nil, "", fmt.Errorf("storage URL %q must not include a query string", rawURL)
		}
		if u.Fragment != "" {
			return nil, "", fmt.Errorf("storage URL %q must not include a fragment", rawURL)
		}
		match := s3HostPattern.FindStringSubmatch(u.Host)
		if match == nil {
			return nil, "", fmt.Errorf(
				"unsupported storage URL host %q (expected <bucket>.s3.<region>.amazonaws.com)",
				u.Host,
			)
		}
		bucket := match[s3HostPattern.SubexpIndex("bucket")]
		region := match[s3HostPattern.SubexpIndex("region")]
		prefix := strings.TrimPrefix(u.Path, "/")
		provider, err := NewS3Provider(S3Config{Bucket: bucket, Region: region})
		if err != nil {
			return nil, "", err
		}
		return provider, prefix, nil

	case "s3":
		return nil, "", fmt.Errorf(
			"use the HTTPS form https://<bucket>.s3.<region>.amazonaws.com/<prefix>",
		)

	default:
		return nil, "", fmt.Errorf("unsupported storage URL scheme %q (expected https)", u.Scheme)
	}
}
