---
title: Block Assets
order: 8
---

# Block Assets Management

Clay's `block assets` commands let you upload, list, and download files associated with your blocks in cloud storage. The interface is platform-agnostic: every command takes a single `--url` flag that names a complete storage location. The URL's scheme tells Clay which backend to use.

## Overview

Block assets are any files a block needs to function, such as:

- Pre-trained block weights
- Configuration files
- Reference data
- Documentation
- Scripts and utilities

## The `--url` contract

All three commands (`upload`, `list`, `download`) take a single `--url <storage-url>` flag. For upload/list it points at the folder. For download it points at the file.

Only AWS S3 virtual-hosted HTTPS URLs are supported:

```
https://<bucket>.s3.<region>.amazonaws.com/<prefix>/
```

The bucket and region are parsed out of the host — the region must be in the URL, so the SDK never has to discover it at runtime. `s3://` URIs and other hosts return a clear error.

## Commands

### Upload Assets

```bash
# Upload a directory
clay block assets upload ./blocks \
  --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1.0.0/

# Upload a single file
clay block assets upload block.pkl \
  --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1.0.0/
```

### Upload catalog media with `upload-catalog`

`clay block assets upload-catalog` publishes the media declared in the `catalog.yaml` in the current working directory (run it from the model repo root). It takes no path argument — only `--url`. Clay:

1. reads the `media:` section (which maps keys to relative file paths),
2. uploads each declared file to `<your --url>/<relative-path>`,
3. rewrites each `media:` value in `catalog.yaml` to the uploaded URL. The rest of the content is carried over unchanged, but the file is re-serialized — comments and formatting are not preserved.
4. uploads the rewritten `catalog.yaml` itself to `<your --url>/catalog.yaml`, so the published catalog lives alongside the media it references.

Bake the block name and version into `--url`; only the media relative path is appended, so the S3 key and the rewritten URL always agree.

The command is idempotent: `media:` values that are already `http(s)` URLs (from a previous run) are skipped. Run this upload before `clay publish` — the catalog is published as-is, so `media:` values left as relative paths will not resolve in the catalog frontend.

Example — given:

```yaml
# catalog.yaml
media:
  thumbnail: catalog_readme/thumbnail.png
  sample_input: catalog_readme/sample_input.png
  sample_output: catalog_readme/sample_output.png
```

running (from the model repo root):

```bash
clay block assets upload-catalog \
  --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1.0.0/
```

uploads `catalog_readme/thumbnail.png` to `.../my-block/v1.0.0/catalog_readme/thumbnail.png` and rewrites the `media:` value to that URL. The three reserved keys `thumbnail`, `sample_input`, and `sample_output` are required.

### List Assets

```bash
clay block assets list --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1.0.0/
```

### Download Assets

`--url` must point at a single file.

```bash
# Download into the current directory (keeps the remote filename)
clay block assets download \
  --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1.0.0/block.pkl

# Download to a specific local path
clay block assets download \
  --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1.0.0/configs/inference.yaml \
  --output ./my-config.yaml
```

## Authentication

### AWS S3

Configure credentials with any of:

1. **Environment variables:**
   ```bash
   export AWS_ACCESS_KEY_ID=your-key-id
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_REGION=us-east-1
   ```

2. **Shared config:** `aws configure`.

3. **IAM role:** automatically used when running on EC2 / ECS / EKS.

## Best Practices

- Encode your organization's layout directly in the `--url` (e.g. `https://<bucket>.s3.<region>.amazonaws.com/blocks/<name>/<version>/`). The CLI doesn't impose a convention.
- Keep related assets together in directories and upload them as a single `clay block assets upload` call.
- Never commit credentials to version control; prefer IAM roles.
- Restrict bucket permissions to what the block workflow actually needs.
- Compress large files before uploading when appropriate.

## Troubleshooting

**`unsupported storage URL scheme` / `unsupported storage URL host`**
Only AWS S3 virtual-hosted HTTPS URLs are supported. Form: `https://<bucket>.s3.<region>.amazonaws.com/<prefix>/`. `s3://` URIs are rejected — encode the bucket and region in the HTTPS host.

**`asset not found`**
Verify `--url` exactly matches the remote path and is case-sensitive.

**Authentication failures**
Confirm AWS credentials are configured (see above) and that they have the required S3 permissions on the target bucket.

**Debug logging**
```bash
export CLAY_DEBUG=true
```
