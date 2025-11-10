# Block Assets Management

Clay provides a comprehensive asset management system for storing and retrieving files associated with your blocks in cloud storage. This feature supports multiple cloud providers (currently S3, with GCS and Azure coming soon) and allows you to organize assets at both the block name level (shared across versions) and version-specific level.

## Overview

Block assets are any files that your model or block needs to function properly, such as:
- Pre-trained model weights
- Configuration files
- Reference data
- Documentation
- Scripts and utilities

## Storage Structure

Assets are organized in a hierarchical structure within your cloud storage:

```
<bucket>/
└── blocks/
    └── <block-name>/
        ├── assets/              # Name-level assets (shared across all versions)
        │   ├── common-config.yaml
        │   ├── shared-data/
        │   └── reference-models/
        └── <version>/
            └── assets/          # Version-specific assets
                ├── model.pkl
                ├── config.yaml
                └── data/
```

### Name-level vs Version-specific Assets

- **Name-level assets** (`blocks/<name>/assets/`): Shared across all versions of a block. Use for common resources that don't change between versions.
- **Version-specific assets** (`blocks/<name>/<version>/assets/`): Specific to a particular version. Use for version-dependent resources like model weights or version-specific configs.

## Commands

### Upload Assets

Upload files or directories to cloud storage:

```bash
# Upload to name-level (shared across versions)
clay block assets upload ./models --name my-block --bucket my-bucket --region us-east-1

# Upload to version-specific location
clay block assets upload ./models --name my-block --version v1.0.0 --bucket my-bucket --region us-east-1

# Upload a single file
clay block assets upload model.pkl --name my-block --version v1.0.0 --bucket my-bucket

# Upload README with template processing
clay block assets upload ./catalog_readme --name my-block --version v1.0.0 \
  --bucket my-bucket --region us-east-1 --readme
```

### Upload with Template Processing

When uploading README or catalog files with the `--readme` flag, Clay will:
1. Process any markdown templates using the `{{addUrl "filename"}}` function
2. Replace template variables with actual URLs based on your bucket and block details
3. Upload the processed files to the specified location

Example:
```bash
# Your catalog_readme/model-README.md contains:
# ![]({{ addUrl "sample_input.png" }})
# This will be processed to:
# ![](https://my-bucket.s3.us-east-1.amazonaws.com/blocks/my-block/v1.0.0/catalog_readme/sample_input.png)

clay block assets upload ./catalog_readme --name my-block --version v1.0.0 \
  --bucket my-bucket --region us-east-1 --readme
```

### List Assets

View all assets stored for a block:

```bash
# List name-level assets
clay block assets list --name my-block --bucket my-bucket --region us-east-1

# List version-specific assets
clay block assets list --name my-block --version v1.0.0 --bucket my-bucket --region us-east-1
```

### Download Assets

Download specific assets to your local filesystem:

```bash
# Download a single file
clay block assets download model.pkl --name my-block --version v1.0.0 \
  --bucket my-bucket --region us-east-1

# Download to a specific location
clay block assets download configs/inference.yaml --name my-block --version v1.0.0 \
  --bucket my-bucket --region us-east-1 --output ./my-config.yaml

# Download with automatic fallback (version-specific → name-level)
clay block assets download common-config.yaml --name my-block --version v1.0.0 \
  --bucket my-bucket --region us-east-1
```

## Authentication

### AWS S3

Configure AWS credentials using one of these methods:

1. **Environment Variables**:
   ```bash
   export AWS_ACCESS_KEY_ID=your-key-id
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_REGION=us-east-1
   ```

2. **AWS CLI Configuration**:
   ```bash
   aws configure
   ```

3. **IAM Role** (when running on EC2 or ECS):
   Automatically uses instance/task role credentials

### Future Providers

- **Google Cloud Storage (GCS)**: Will use `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- **Azure Blob Storage**: Will use `AZURE_STORAGE_ACCOUNT` and `AZURE_STORAGE_KEY` environment variables

## Best Practices

### 1. Asset Organization

- Keep related assets together in directories
- Use descriptive names for assets
- Maintain consistent naming conventions across versions

### 2. Version Management

- Use version-specific assets for anything that changes between releases
- Use name-level assets for shared, immutable resources
- Document which assets are required for each version

### 3. Security

- Never commit credentials to version control
- Use IAM roles when possible instead of access keys
- Restrict bucket permissions to only what's necessary
- Enable bucket versioning for critical assets

### 4. Performance

- Compress large files before uploading when appropriate
- Use appropriate storage classes for infrequently accessed data
- Consider using CDN for frequently accessed assets

## Examples

### Complete Workflow Example

```bash
# 1. Upload model weights for a new version
clay block assets upload ./trained_models/v2.0.0/ \
  --name image-classifier --version v2.0.0 \
  --bucket ml-models --region us-west-2

# 2. Upload shared configuration
clay block assets upload ./configs/base_config.yaml \
  --name image-classifier \
  --bucket ml-models --region us-west-2

# 3. List all assets to verify
clay block assets list --name image-classifier --version v2.0.0 \
  --bucket ml-models --region us-west-2

# 4. Download model for inference
clay block assets download model.pkl \
  --name image-classifier --version v2.0.0 \
  --bucket ml-models --region us-west-2 \
  --output ./model_cache/
```

### Integration with Model Code

```python
import os
from clay_utils import download_block_asset  # hypothetical utility

class MyModel:
    def __init__(self, block_name, version):
        self.block_name = block_name
        self.version = version
        
    def load_model(self):
        # Download model weights if not cached
        model_path = f"./cache/{self.version}/model.pkl"
        if not os.path.exists(model_path):
            # This would use clay CLI or SDK internally
            download_block_asset(
                asset_path="model.pkl",
                block_name=self.block_name,
                version=self.version,
                output_path=model_path
            )
        
        # Load the model
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
```

## Troubleshooting

### Common Issues

1. **"Asset not found" error**
   - Verify the asset path is correct (case-sensitive)
   - Check if uploading to version-specific vs name-level location
   - Ensure the asset was uploaded successfully

2. **Authentication failures**
   - Verify AWS credentials are configured correctly
   - Check if the credentials have necessary S3 permissions
   - Ensure the bucket exists and is accessible

3. **Upload failures**
   - Check available disk space
   - Verify network connectivity
   - Ensure the local file/directory exists
   - Check S3 bucket permissions

### Debug Mode

For detailed logging, set the environment variable:
```bash
export CLAY_DEBUG=true
```