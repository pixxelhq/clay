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

# Parse a template and upload the directory
clay block assets upload ./docs \
  --parse README.md:parsed.md \
  --url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1.0.0/catalog_readme/
```

### Upload with `--parse` Template Processing

When you pass `--parse`, Clay renders the named file through Go's `text/template` engine before uploading the directory. The format is:

```
--parse <input>[:<output>]
```

Paths are relative to the `<path>` argument (the upload directory). If `<output>` is omitted, it defaults to `<name>.parsed<ext>` (e.g. `README.md` becomes `README.parsed.md`).

The template can reference a helper:

- `{{ addUrl "filename" }}` — expands to `<your --url>/filename`.

This lets you write relative asset references that resolve to absolute URLs at upload time.

Example:

```markdown
<!-- docs/README.md -->
![sample]({{ addUrl "sample_input.png" }})
```

With `--url https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1.0.0/catalog_readme/`, this renders to:

```markdown
![sample](https://my-bucket.s3.us-east-1.amazonaws.com/my-block/v1.0.0/catalog_readme/sample_input.png)
```

The rendered output is written next to the template and uploaded along with the rest of the folder.

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
