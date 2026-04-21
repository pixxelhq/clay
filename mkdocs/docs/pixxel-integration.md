# Pixxel Platform Integration

This guide walks you through the complete workflow for developing and deploying ML blocks at Pixxel using Clay.

!!! tip "Quick Navigation"
    - **First time?** Start with [One-Time Setup](#one-time-setup)
    - **Starting a new block?** Jump to [Create Your Block Project](#step-1-create-your-block-project)
    - **Ready to deploy?** Go to [Deploy to Orchestrator](#step-5-deploy-to-orchestrator)

---

## How It Works at Pixxel

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Create Block   │────▶│  Build & Test   │────▶│ Push to Registry│────▶│Deploy to Orchestrator│
│  (clay create)  │     │  (clay build)   │     │ (GitHub Actions)│     │    (Platform)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Key Components:**

| Component | What it does |
|-----------|--------------|
| **Clay** | Framework for packaging your block |
| **Orchestrator** | Orchestrates block execution on Kubernetes |
| **Platform** | Platform where users discover and run blocks |
| **Clay Registry** | Stores block metadata and specifications |

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
aws sso login --profile=your-aws-profile

# If credentials aren't detected, export the profile
export AWS_PROFILE=your-aws-profile
```

!!! success "Setup Complete!"
    You're now ready to create block projects.

---

## Creating and Deploying a Block

Follow these steps to create a new block and deploy it to Orchestrator.

### Step 1: Create Your Block Project

```bash
# Create a new project
clay new ./MyBlock MyBlock

# Navigate to the project
cd MyBlock

# Initialize git repository
git init

# Set up the development environment
make setup
```

This creates the following structure:

```
MyBlock/
├── src/
│   ├── block.py          # Your block code goes here
│   ├── entry.py          # Entry point (don't modify)
│   ├── test_block.py     # Local testing script
│   └── sample_block_inputs.json
├── clay.yaml             # Block specification
├── requirements.txt      # Python dependencies
└── Makefile              # Build commands
```

### Step 2: Implement Your Block

Edit `src/block.py` to implement your block logic:

```python
from clay.core import BlockWrapper
import datatypes

class MyBlock(BlockWrapper):
    def setup(self, **parameters):
        """Initialize your block (load weights, etc.)"""
        self.logger.info("Block initialized")

    async def preprocess(self, input_raster: datatypes.Raster):
        """Validate and prepare inputs"""
        self.logger.info(f"Processing: {input_raster.value}")
        return {"raster": input_raster}

    async def inference(self, raster):
        """Run your block logic"""
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

### Step 3: Configure Your Block Specification

Edit `clay.yaml`:

```yaml
apiVersion: 0.0.1
kind: block
type: processing
name: myblock              # Must be lowercase, unique
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
 clay run  -e INPUT_JSON=\"$(cat <SAMPLE_input_file.json>)\" myblock:0.0.1
```

!!! note "Expected Output"
    You'll see logs for block initialization, preprocessing, inference, and postprocessing. A warning about missing `ORCHESTRATOR_URL` is normal for local runs.

### Step 5: Deploy to Orchestrator

#### 5a. Set Up GitHub Repository (First time only)

1. **Create GitHub repo** at `github.com/example/<your-block-name>`

2. **Add repository secrets** at `Settings > Secrets and variables > Actions`:

    | Secret | How to get it |
    |--------|---------------|
    | `CLAY_BIN_DOWNLOAD_TOKEN` | Your GitHub PAT with `repo` and `workflow` permissions |
    | `AUTH_ORG_IDS` | Contact MLOps team |
    | `AUTH_SUB` | Contact MLOps team |

3. **Register container registry** - Create a PR on [infra](https://github.com/example/infra):

    Edit `infra/aws/core/production/infrastructure/container_registry/variables.tf`:
    ```hcl
    "your-block-name" = {
      github = "https://github.com/example/your-block-name"
    }
    ```

#### 5b. Push to GitHub

```bash
git add .
git commit -m "Initial block implementation"
git remote add origin git@github.com:example/<your-block-name>.git
git push -u origin main
```

#### 5c. Publish to Clay Registry

1. Go to your repo's **Actions** tab
2. Select **"Publish block to Clay registry"** workflow
3. Click **Run workflow**:
    - Branch: `main`
    - Version: `v0.0.1` (must match clay.yaml)
    - Docker tag: leave empty for production, use `dev-*` prefix for dev builds

4. Verify publication:
    ```bash
    clay block list --env dev
    clay block describe myblock --version v0.0.1 --env dev
    ```

#### 5d. Deploy to Platform

1. Clone [block-configs](https://github.com/example/block-configs)
2. Create/edit your block's config files:
    - `<block-name>/development.yaml`
    - `<block-name>/staging.yaml`
    - `<block-name>/production.yaml`
3. Create PR and tag reviewers: `@maintainers`, `@contributor`, `@contributor`
4. After merge, run **"Onboard block to Platform platform"** workflow

!!! success "Deployment Complete!"
    Your block is now available on the Platform platform.

---

## Quick Reference

### Common Commands

```bash
# Create new project
clay new ./BlockName BlockName

# Build Docker image
clay build

# Run locally
clay run  -e INPUT_JSON=\"$(cat <SAMPLE_input_file.json>)\" <block>:<version>
# List blocks in registry
clay block list --env dev|stg|prod

# Describe a block
clay block describe <name> --version <version> --env dev

# Add block to Orchestrator (production)
clay add block clay.yaml --env prod

# Upload block README
clay block assets upload catalog_readme/ --parse README.md:parsed.md \
  --url https://<bucket>.s3.<region>.amazonaws.com/<block-name>/<version>/catalog_readme/
```

### Environment-Specific Deployment

| Environment | Method | Notes |
|-------------|--------|-------|
| **dev** | GitHub Actions | Use `dev-*` docker tag prefix (auto-deleted after 1 month) |
| **stg** | GitHub Actions | Version creates git tag + docker tag |
| **prod** | CLI or GitHub Actions | Requires approval |

### Block Documentation

Update `docs/README.md`:

```markdown
---
name: Your Block Name
author: your-name
input-img: ![]({{ addUrl "sample_input.png" }})
output-img: ![]({{ addUrl "sample_output.png" }})
inputs: {input1: "description", input2: "description"}
outputs: {output1: "description"}
---

## Description
What your block does...

## Usage
How to use it...
```

Upload with:
```bash
clay block assets upload ./docs --parse README.md:parsed.md \
  --url https://<bucket>.s3.<region>.amazonaws.com/<block-name>/<version>/docs/
```

---

## Troubleshooting

### AWS Authentication Issues

```bash
# Re-login to AWS SSO
aws sso login --profile=your-aws-profile

# Export profile if not detected
export AWS_PROFILE=your-aws-profile
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
| Input file not found | Check path in sample_block_inputs.json |
| Block crashes | Check logs, add more `self.logger.info()` statements |

---

## Getting Help

| Topic | Contact |
|-------|---------|
| Infrastructure, CI/CD | **MLOps Team** |
| Platform integration | **Platform Team** |
| Block development | **Analytics Team** |

### Internal Resources

- [Block Configs Repository](https://github.com/example/block-configs)
- [infra Infrastructure](https://github.com/example/infra)
- Monitoring Dashboards - Ask MLOps team for access

---