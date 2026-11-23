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

All four commands (`upload`, `upload-catalog`, `list`, `download`) take a single `--url <storage-url>` flag. For `upload`, `upload-catalog` and `list` it points at the folder. For `download` it points at the file.

Only AWS S3 virtual-hosted HTTPS URLs are supported:

```
https://<bucket>.s3.<region>.amazonaws.com/<prefix>/
```

The bucket and region are parsed out of the host. The region must be in the URL. Bucket names that contain dots are rejected. `s3://` URIs and other hosts return an error. Support for `s3://` URLs and custom S3 endpoints is planned.

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

`clay block assets upload-catalog` publishes the media declared in the `catalog.yaml` in the current working directory (run it from the model repo root). It takes no path argument — only `--url`. To start a `catalog.yaml`, create the project with `clay new <path> --with catalog`. Clay:

1. reads the `media:` section (which maps keys to relative file paths). The section must not be empty.
2. uploads each file to `<your --url>/<key>/<filename>`. The local folders are dropped.
3. makes a copy of `catalog.yaml` with each `media:` value set to its uploaded URL. The copy is re-serialized, so comments and formatting are not kept in it.
4. uploads that copy to `<your --url>/catalog.yaml`, next to the media, and prints its URL.

Your `catalog.yaml` is not changed.

Bake the block name and version into `--url`. Only `<key>/<filename>` is appended to it.

`media:` values that are already `http(s)` URLs are not uploaded again. Local paths are uploaded again on every run.

`clay publish` does not read `catalog.yaml`. Pass the printed catalog URL to `clay publish --catalog-url`.

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

uploads `catalog_readme/thumbnail.png` to `.../my-block/v1.0.0/thumbnail/thumbnail.png`, and sets the `media:` value in the uploaded copy to that URL. It then prints `.../my-block/v1.0.0/catalog.yaml`. Clay does not require any particular keys.

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

Clay uses the standard AWS SDK credential chain. Configure credentials with any of:

1. **Environment variables:**
   ```bash
   export AWS_ACCESS_KEY_ID=your-key-id
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   ```

2. **Shared config:** `aws configure`, or a named profile with `AWS_PROFILE` (SSO profiles work too).

3. **IAM role:** used automatically when running on EC2 / ECS / EKS.

The region always comes from the `--url` host. `AWS_REGION` is not needed.

## Best Practices

- Encode your organization's layout directly in the `--url` (e.g. `https://<bucket>.s3.<region>.amazonaws.com/blocks/<name>/<version>/`). The CLI doesn't impose a convention.
- Keep related assets together in directories and upload them as a single `clay block assets upload` call.
- Never commit credentials to version control; prefer IAM roles.
- Restrict bucket permissions to what the block workflow actually needs.
- Compress large files before uploading when appropriate.

## Troubleshooting

**`unsupported storage URL scheme` / `unsupported storage URL host`**
Only AWS S3 virtual-hosted HTTPS URLs are supported. Form: `https://<bucket>.s3.<region>.amazonaws.com/<prefix>/`. Bucket names with dots do not match this form.

**`use the HTTPS form https://<bucket>.s3.<region>.amazonaws.com/<prefix>`**
You passed an `s3://` URI. Put the bucket and region in the HTTPS host instead.

**`asset not found`**
Verify `--url` exactly matches the remote path and is case-sensitive.

**Authentication failures**
For example `NoCredentialProviders: no valid providers in chain`, `InvalidAccessKeyId` or `AccessDenied`. Confirm AWS credentials are configured (see [Authentication](#authentication)) and that they have the required S3 permissions on the target bucket.
