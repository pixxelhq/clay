# Clay Project Contributing guide

## Prerequisites

### System Requirements
- Go (version 1.20 or later)
- Python (version 3.8 or later)
- Docker
- AWS CLI
- pre-commit
- pip

### AWS Setup
- Configure AWS CLI with appropriate credentials
- Access to AWS CodeArtifact
- Permissions for REDACTED-ARTIFACTORY

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd clay
   ```

2. **Install Development Dependencies**
   ```bash
   make init
   ```
   This command will:
   - Install development requirements
   - Set up pre-commit hooks
   - Configure commit message hooks

3. **Initialize Requirements**
   ```bash
   make init-requirements
   ```
   Generates CodeArtifact authentication token and installs project requirements

## Development Workflow

### Building the Project

#### Build Package
```bash
make package
```
Creates distributable Python package in the `build/` directory.

### Testing

#### Run All Tests
```bash
make test
```
Executes both Go and Python tests.

#### Language-Specific Tests
- Python Tests: `make test-python`
- Go Tests: `make test-go`
- Registry Tests: `make test-registry`

### Code Quality

#### Formatting
```bash
make format
```
- Lints Python code using Ruff
- Formats code automatically
- Runs pre-commit checks

#### Pre-commit Checks
```bash
make pre-commit
```
Manually triggers pre-commit hooks.

### Documentation

#### Build Documentation
```bash
make build-docs
```
Builds project documentation using MkDocs.

#### Serve Documentation Locally
```bash
make serve-docs
```
Builds and serves documentation on a local development server.

#### Spell Check Documentation
```bash
make spell-check-docs
```
Checks spelling in documentation markdown files.

### Build Binaries

#### Generate Cross-Platform Binaries
```bash
make go-binaries
```
Creates binaries for:
- macOS (amd64 and arm64)
- Windows (amd64)
- Linux (amd64 and arm64)

Binaries are output to the `./bin` directory.

### Integration Testing

#### Test with Runner
```bash
make test-with-runner
```
Runs integration tests using Docker Compose with Kubernetes executor.

#### Test with Runner V2
```bash
make test-with-runnerv2
```
Runs integration tests using Docker Compose with Argo executor.

### Cleanup

#### Tear Down Test Environment
```bash
make tear-down
```
Removes Docker Compose resources and temporary files.

## Contributing

1. Install development dependencies
2. Run pre-commit hooks
3. Write tests for new features
4. Ensure all tests pass before submitting a PR

## Troubleshooting

- Ensure AWS CLI is configured correctly
- Check network connectivity to AWS CodeArtifact
- Verify Python and Go versions match prerequisites

## License
