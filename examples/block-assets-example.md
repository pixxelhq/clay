# Block Assets Management Example

This example demonstrates how to use Clay's block asset management feature to upload, list, and download assets associated with your blocks.

## Prerequisites

- Clay CLI installed
- AWS credentials configured (for S3 provider)
- An S3 bucket created

## Usage Examples

### 1. Upload Assets

Upload a single file to a block (name-level, shared across versions):
```bash
clay block assets upload ./model.pkl --name image-classifier --bucket my-clay-assets --region us-east-1
```

Upload a directory to a specific version:
```bash
clay block assets upload ./models --name image-classifier --version v1.0.0 --bucket my-clay-assets --region us-east-1
```

### 2. List Assets

List all assets for a block (name-level):
```bash
clay block assets list --name image-classifier --bucket my-clay-assets --region us-east-1
```

List assets for a specific version:
```bash
clay block assets list --name image-classifier --version v1.0.0 --bucket my-clay-assets --region us-east-1
```

### 3. Download Assets

Download a specific asset:
```bash
clay block assets download model.pkl --name image-classifier --version v1.0.0 --bucket my-clay-assets --region us-east-1
```

Download to a specific location:
```bash
clay block assets download configs/inference.yaml --name image-classifier --version v1.0.0 \
  --bucket my-clay-assets --region us-east-1 --output ./my-config.yaml
```

## Storage Structure

Assets are organized in the following structure:

```
bucket/
└── blocks/
    └── <block-name>/
        ├── assets/              # Name-level assets (shared)
        │   ├── common-config.yaml
        │   └── shared-models/
        └── <version>/
            └── assets/          # Version-specific assets
                ├── model.pkl
                └── configs/
```

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

### Future Providers
- **GCS**: Will use `GOOGLE_APPLICATION_CREDENTIALS`
- **Azure**: Will use `AZURE_STORAGE_ACCOUNT` and `AZURE_STORAGE_KEY`

## Best Practices

1. **Use version-specific assets** for models and configs that change between versions
2. **Use name-level assets** for shared resources like common configurations or data
3. **Always specify region** for S3 to avoid defaulting to us-east-1
4. **Version fallback**: When downloading with a version specified, the system will check version-specific assets first, then fall back to name-level assets if not found