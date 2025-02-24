# Release Process

This document describes the release process for the Clay service. The deployment process is automated using GitHub Actions and follows different patterns for each component.

## Deployment Environments
- **Staging**: Used for testing before production deployments for Clay Registry
- **Production**: Production environment for all Clay components

## Deployment Flow

### 1. Clay CLI Release
- **Trigger**: Automatically when any tag is pushed to the repository
- **Process**:
  1. Checks out the repository
  2. Sets up Go environment
  3. Configures private token for GitHub access
  4. Runs GoReleaser to build and release the CLI

To release the CLI:
```bash
# tag name depends on the version to be deployed next, bump up according to https://semver.org/
git tag v1.2.3
git push origin v1.2.3
```

### 2. Clay Python SDK Release
- **Trigger**: Manual workflow dispatch in GitHub Actions, it uses `./python/clay/__version__.py` file to pick the version of clay python sdk
- **Process**:
  1. Configures AWS credentials for CodeArtifact access
  2. Sets up Python environment (3.8.1)
  3. Builds the Python package from the `/python` directory
  4. Uploads the package to AWS CodeArtifact Python repository

To release the Python SDK:
1. Go to GitHub Actions
2. Select "[Manual] Release clay python sdk" workflow
3. Click "Run workflow"
4. Monitor the workflow execution

### 3. Clay Registry Deployment
- **Trigger**: Manual workflow dispatch in GitHub Actions
- **Process**:
  1. Builds and pushes Docker image to ECR
  2. Deploys to staging environment (cluster-staging cluster)
  3. Requires successful staging deployment for production
  4. Deploys to production environment (cluster-prod cluster)

To deploy the Registry:
1. Go to GitHub Actions
2. Select "[Manual] Deploy registry" workflow
3. Click "Run workflow"
4. Approve staging deployment if required
5. Approve production deployment after staging is successful

### 4. Clay Documentation Deployment
- **Trigger**: 
  - Automatically when changes are pushed to `mkdocs/` directory on main branch
  - Automatically when a GitHub Release is published
  - Manually via workflow dispatch with optional tag parameter
- **Process**:
  1. Builds Docker image with documentation
  2. Pushes image to ECR
  3. Deploys directly to production documentation site

## Deployment Process Details
Each deployment includes:
1. Building Docker images and pushing to ECR where applicable
2. Fetching environment-specific configurations from Vault for Registry deployment
3. Deploying using Helm with environment-specific values
4. Slack notifications for Registry deployment status

## Monitoring Deployments
- Monitor deployments in GitHub Actions tab
- Check deployment status in Slack notifications for Registry deployments
- Each environment deployment has its own workflow job that can be monitored separately

## Important Notes
- All deployments require appropriate AWS IAM roles and permissions
- Vault tokens are required for accessing environment configurations for Registry deployment
- Registry deployment uses different AWS accounts for staging and production environments
- Deployment announcements for Registry are automatically posted to Slack
- Helm deployments use the raystack/app chart with environment-specific configurations
- Python SDK is published to AWS CodeArtifact, not PyPI