# Block Assets Management Example

This example demonstrates how to use Clay's block asset management feature to upload, list, and download assets associated with your blocks.

## Prerequisites

- Clay CLI installed
- An S3 bucket created
- AWS credentials configured. The `clay block assets` commands only support
  AWS S3 virtual-hosted HTTPS URLs — runtime block I/O can use any
  S3-compatible backend, but asset management is AWS-S3-specific.
  Any credential source the AWS SDK recognises works:
  environment variables (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`),
  `AWS_PROFILE` + `~/.aws/config` (including SSO profiles), or IAM instance
  roles. See the [Authentication](#authentication) section below for details.

## Usage Examples

### 1. Upload Assets

Upload a single file:
```bash
clay block assets upload ./block.pkl \
  --url https://my-clay-assets.s3.us-east-1.amazonaws.com/image-classifier/v1.0.0/
```

Upload a directory:
```bash
clay block assets upload ./weights \
  --url https://my-clay-assets.s3.us-east-1.amazonaws.com/image-classifier/v1.0.0/
```

Upload catalog media and rewrite `catalog.yaml` in place (uploads each file in its `media:` section, rewrites the values to absolute URLs, then uploads the catalog itself). Run it from the model repo root — it reads `catalog.yaml` from the current directory and takes no path argument:
```bash
clay block assets upload-catalog \
  --url https://my-clay-assets.s3.us-east-1.amazonaws.com/image-classifier/v1.0.0/
```

### 2. List Assets

List all assets at a storage location:
```bash
clay block assets list \
  --url https://my-clay-assets.s3.us-east-1.amazonaws.com/image-classifier/v1.0.0/
```

### 3. Download Assets

Download a specific asset:
```bash
clay block assets download \
  --url https://my-clay-assets.s3.us-east-1.amazonaws.com/image-classifier/v1.0.0/block.pkl
```

Download to a specific location:
```bash
clay block assets download \
  --url https://my-clay-assets.s3.us-east-1.amazonaws.com/image-classifier/v1.0.0/configs/inference.yaml \
  --output ./my-config.yaml
```

## URL Format

All commands take a single `--url` flag. Only AWS S3 virtual-hosted HTTPS URLs are supported:

```
https://<bucket>.s3.<region>.amazonaws.com/<prefix>/
```

The bucket and region are parsed from the hostname. `s3://` URIs are not supported.

## Authentication

### AWS S3
Set AWS credentials using environment variables:
```bash
export AWS_ACCESS_KEY_ID=your-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1
```

Or use AWS CLI configuration:
```bash
aws configure
```

## Best Practices

1. Encode your layout directly in the `--url` (e.g. `.../blocks/<name>/<version>/`). The CLI does not impose a convention.
2. Keep related assets together in directories and upload them in a single call.
3. Never commit credentials to version control; prefer IAM roles.
4. Compress large files before uploading when appropriate.
