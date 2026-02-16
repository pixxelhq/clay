# Pixxel Platform Integration

This guide walks you through the complete workflow for developing and deploying ML models at Pixxel using Clay.

!!! tip "Quick Navigation"
    - **First time?** Start with [One-Time Setup](#one-time-setup)
    - **Starting a new model?** Jump to [Create Your Model Project](#step-1-create-your-model-project)
    - **Ready to deploy?** Go to [Deploy to Orchestrator](#step-5-deploy-to-orchestrator)

---

## How It Works at Pixxel

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Create Model   │────▶│  Build & Test   │────▶│ Push to Registry│────▶│ Deploy to Orchestrator│
│  (clay create)  │     │  (clay build)   │     │ (GitHub Actions)│     │    (Platform)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Key Components:**

| Component | What it does |
|-----------|--------------|
| **Clay** | Framework for packaging your model |
| **Orchestrator** | Orchestrates model execution on Kubernetes |
| **Platform** | Platform where users discover and run models |
| **Clay Registry** | Stores model metadata and specifications |

**Environments:**

| Environment | Purpose | Who can access |
|-------------|---------|----------------|
| **dev** | Testing and iteration | Developers |
| **stg** | Pre-production validation | Internal teams |
| **prod** | Customer-facing | Everyone |

---

## One-Time Setup

Complete these steps once to set up your development environment.

### Prerequisites Checklist

- [ ] macOS or Linux machine
- [ ] Docker installed and running
- [ ] Python >= 3.9
- [ ] Access to Pixxel GitHub organization
- [ ] AWS CLI installed

### Step 1: Create GitHub Personal Access Token

1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Select scopes: `repo`, `write:packages`, `read:packages`
4. Copy the token

### Step 2: Install Clay CLI

```bash
# Set your GitHub token (add to ~/.bashrc or ~/.zshrc for persistence)
export HOMEBREW_GITHUB_API_TOKEN=<your-github-token>

# Add Pixxel's Homebrew tap
brew tap example/tap

# Install Clay
brew install --formula example/tap/clay

# Verify installation
clay --version
```

??? note "Upgrading Clay"
    ```bash
    brew upgrade --formula example/tap/clay
    ```

### Step 3: Configure AWS Access

```bash
# Login to AWS SSO
aws sso login --profile=d-platform-services

# If credentials aren't detected, export the profile
export AWS_PROFILE=d-platform-services
```

!!! success "Setup Complete!"
    You're now ready to create model projects.

---

## Creating and Deploying a Model

Follow these steps to create a new model and deploy it to Orchestrator.

### Step 1: Create Your Model Project

```bash
# Create a new project
clay create project ./MyModel MyModel

# Navigate to the project
cd MyModel

# Initialize git repository
git init

# Set up the development environment
make setup
```

This creates the following structure:

```
MyModel/
├── src/
│   ├── model.py          # Your model code goes here
│   ├── entry.py          # Entry point (don't modify)
│   ├── test_model.py     # Local testing script
│   └── sample_model_inputs.json
├── clay.yaml             # Model specification
├── requirements.txt      # Python dependencies
├── Makefile             # Build commands
└── .github/workflows/   # CI/CD pipelines
```

### Step 2: Implement Your Model

Edit `src/model.py` to implement your model logic:

```python
from clay.core import ModelWrapper
import datatypes

class MyModel(ModelWrapper):
    def setup(self, **parameters):
        """Initialize your model (load weights, etc.)"""
        self.logger.info("Model initialized")

    async def preprocess(self, input_raster: datatypes.Raster):
        """Validate and prepare inputs"""
        self.logger.info(f"Processing: {input_raster.value}")
        return {"raster": input_raster}

    async def inference(self, raster):
        """Run your model logic"""
        # Your inference code here
        return {"result": processed_data}

    async def postprocess(self, result):
        """Format outputs"""
        return {
            "output": datatypes.Raster(
                name="result",
                value="output.tif",
                is_artifact=True
            )
        }
```

### Step 3: Configure Your Model Specification

Edit `clay.yaml`:

```yaml
apiVersion: 0.0.1
kind: block
type: processing
name: mymodel              # Must be lowercase, unique
version: v0.0.1            # Semantic versioning
author: your-name

tags:
  - imagery
  - your-tag

parameters:
  - name: threshold
    type: float
    default: 0.5

inputs:
  - name: input_raster
    format: raster
    type: url
    properties:
      collection: sentinel-2-l2a

outputs:
  - name: result
    format: raster
    type: url

build:
  python-version: "3.10"
  gdal: true
  requirements: requirements.txt

gpu: false
```

### Step 4: Build and Test Locally

```bash
# Build Docker image
clay build

# Test locally with sample inputs
 clay run  -e INPUT_JSON=\"$(cat <SAMPLE_input_file.json>)\" mymodel:0.0.1
```

!!! note "Expected Output"
    You'll see logs for model initialization, preprocessing, inference, and postprocessing. A warning about missing `ORCHESTRATOR_URL` is normal for local runs.

!!! tip "Benchmark Your Model"
    Before deploying to production, benchmark your model to determine optimal CPU and memory limits for Kubernetes. This helps with accurate pricing and resource allocation. See [Benchmarking](benchmarking.md) for details on using mbench with GitHub Actions.

### Step 5: Deploy to Orchestrator

#### 5a. Set Up GitHub Repository (First time only)

1. **Create GitHub repo** at `github.com/example/<your-model-name>`

2. **Add repository secrets** at `Settings > Secrets and variables > Actions`:

    | Secret | How to get it |
    |--------|---------------|
    | `CLAY_BIN_DOWNLOAD_TOKEN` | Your GitHub PAT with `repo` and `workflow` permissions |
    | `AUTH_ORG_IDS` | Contact MLOps team |
    | `AUTH_SUB` | Contact MLOps team |

3. **Register container registry** - Create a PR on [infra](https://github.com/example/infra):

    Edit `infra/aws/core/production/infrastructure/container_registry/variables.tf`:
    ```hcl
    "your-model-name" = {
      github = "https://github.com/example/your-model-name"
    }
    ```

#### 5b. Push to GitHub

```bash
git add .
git commit -m "Initial model implementation"
git remote add origin git@github.com:example/<your-model-name>.git
git push -u origin main
```

#### 5c. Publish to Clay Registry

1. Go to your repo's **Actions** tab
2. Select **"Publish model to Clay registry"** workflow
3. Click **Run workflow**:
    - Branch: `main`
    - Version: `v0.0.1` (must match clay.yaml)
    - Docker tag: leave empty for production, use `dev-*` prefix for dev builds

4. Verify publication:
    ```bash
    clay block list --env dev
    clay block describe mymodel --version v0.0.1 --env dev
    ```

#### 5d. Deploy to Platform

1. Clone [model-configs](https://github.com/example/model-configs)
2. Create/edit your model's config files:
    - `<model-name>/development.yaml`
    - `<model-name>/staging.yaml`
    - `<model-name>/production.yaml`
3. Create PR and tag reviewers: `@maintainers`, `@contributor`, `@contributor`
4. After merge, run **"Onboard model to Platform platform"** workflow

!!! success "Deployment Complete!"
    Your model is now available on the Platform platform.

---

## Quick Reference

### Common Commands

```bash
# Create new project
clay create project ./ModelName ModelName

# Build Docker image
clay build

# Run locally
clay run  -e INPUT_JSON=\"$(cat <SAMPLE_input_file.json>)\" <model>:<version>
# List blocks in registry
clay block list --env dev|stg|prod

# Describe a block
clay block describe <name> --version <version> --env dev

# Add block to Orchestrator (production)
clay add block clay.yaml --env prod

# Upload model README
clay upload readme --name <model-name> --version <version>
```

### Environment-Specific Deployment

| Environment | Method | Notes |
|-------------|--------|-------|
| **dev** | GitHub Actions | Use `dev-*` docker tag prefix (auto-deleted after 1 month) |
| **stg** | GitHub Actions | Version creates git tag + docker tag |
| **prod** | CLI or GitHub Actions | Requires approval |

### Model Documentation

Update `catalog_readme/model-README.md`:

```markdown
---
name: Your Model Name
author: your-name
input-img: ![]({{ addUrl "sample_input.png" }})
output-img: ![]({{ addUrl "sample_output.png" }})
inputs: {input1: "description", input2: "description"}
outputs: {output1: "description"}
---

## Description
What your model does...

## Usage
How to use it...
```

Upload with:
```bash
clay upload readme --name <model-name> --version <version>
```

---

## Troubleshooting

### AWS Authentication Issues

```bash
# Re-login to AWS SSO
aws sso login --profile=d-platform-services

# Export profile if not detected
export AWS_PROFILE=d-platform-services
```

### Build Failures

| Issue | Solution |
|-------|----------|
| Docker not running | Start Docker Desktop |
| CodeArtifact auth failed | Re-run `aws sso login` |
| Invalid clay.yaml | Check YAML syntax and required fields |
| Missing dependencies | Update requirements.txt |

### Deployment Failures

| Issue | Solution |
|-------|----------|
| GitHub Actions failed | Check repository secrets are set |
| Registry publication failed | Verify version format (semver) |
| Platform deployment failed | Ensure registry publication succeeded first |

### Local Testing Issues

| Issue | Solution |
|-------|----------|
| `ORCHESTRATOR_URL` warning | Normal for local runs, ignore it |
| Input file not found | Check path in sample_model_inputs.json |
| Model crashes | Check logs, add more `self.logger.info()` statements |

---

## Getting Help

| Topic | Contact |
|-------|---------|
| Infrastructure, CI/CD | **MLOps Team** |
| Platform integration | **Platform Team** |
| Model development | **Analytics Team** |

### Internal Resources

- [Model Configs Repository](https://github.com/example/model-configs)
- [infra Infrastructure](https://github.com/example/infra)
- [Benchmarking Guide](benchmarking.md) - Measure CPU, RAM, and runtime for pricing and resource limits
- Monitoring Dashboards - Ask MLOps team for access

---