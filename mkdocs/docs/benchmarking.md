# Benchmarking
In the realm of machine learning, benchmarking isn't just a task—it's an essential process to gauge the hunger of your blocks for resources.
We're talking about maximum CPU, RAM, and runtime here.
These aren't just numbers; they're the backbone of your strategy to price each block run accurately, based on the area it covers, and to set Kubernetes resource limits like a pro.
<br>Now, let's dial down the manual labor and crank up efficiency with GitHub Actions. Here’s your straightforward guide to integrating mbench for automated benchmarking bliss.

## The Why: Benchmarking's Role in the Block Ecosystem
mbench swings into action to capture the peak performance metrics of your machine learning blocks.
<br>This isn't about vanity; it's about:

1. Crafting precise, fair pricing for block runs in specific areas of interest (AOIs) based on their resource consumption.
2. Setting Kubernetes resource limits with confidence, striking the perfect balance between generosity and frugality.

## Preparing Input Data
Before initiating the benchmarking process, prepare a directory containing JSON files (input-file-directory-path).
These files represent different input scenarios for the clay-wrapped block, enabling comprehensive testing across varied data sets.
This preparatory step is crucial for local testing before deployment.

## Setting Up Your GitHub Actions Workflow
Integrating mbench into your GitHub Actions involves a series of steps designed to configure the environment, check out the code, and execute the benchmarking tool.
Here’s a breakdown of each step:

### Step 1: Configure AWS Credentials
Since mbench operates on a dev Kubernetes (K8s) cluster hosted on AWS, the first step involves setting up AWS credentials.
This allows GitHub Actions to interact with AWS services, deploying and managing resources as needed.

```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v2
  with:
    aws-region: us-east-2
    role-to-assume: arn:aws:iam::REDACTED:role/REDACTED
```

### Step 2: Checkout Code
Following AWS configuration, the next step is to check out the repository containing your block and mbench configuration.
This makes the necessary files available for the benchmarking process.
```yaml
- name: Checkout
  uses: actions/checkout@v2
```

### Step 3: Execute mbench
Finally, run the mbench script with the appropriate parameters. This step uses the previously checked-out files and AWS credentials to execute the block benchmarking on the dev K8s cluster.

```yaml
- name: Run mbench
  uses: example/mbench@main
  with:
    id: "unique-benchmark-id"
    mem-limits: "2Gi"  # Kubernetes-style formatting
    cpu-limits: "1000m"  # Kubernetes-style formatting
    docker-block-image-url: "docker-image-url"
    block-name: "block-name"
    input-file-directory-path: "path-to-your-inputs"
```

Each parameter serves a specific function:

1. id: A unique identifier for the benchmark run.
2. mem-limits and cpu-limits: Specify the maximum memory and CPU resources available for the job, adhering to Kubernetes formatting (e.g., Gi for memory, m for CPU).
3. docker-block-image-url: The URL of the Docker image containing the block to be benchmarked.
4. block-name: The name of the block being tested.
5. input-file-directory-path: The path to the directory containing input JSON files for the block.

#### Sample completed workflow
```yaml
name: Run Benchmarks

on:
  workflow_dispatch:
    inputs:
      benchmark-id:
        description: "docker tag"
        required: true
      mem-limits:
        description: "Push block spec to orchestrator"
        required: true
      cpu-limits:
        description: "Push block spec to orchestrator"
        required: true
      docker-block-image-tag:
        description: "Push block spec to orchestrator"
        required: true
      input-file-directory-path:
        required: false
        default: "./tests/inputs"

permissions:
  id-token: write
  contents: read

jobs:
  run_benchmarks:
    runs-on: [ubuntu-latest]
    steps:
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::REDACTED:role/REDACTED
          audience: https://github.com/pixxelhq
          aws-region: ${{ secrets.AWS_DEFAULT_REGION }}
      - name: Checkout
        uses: actions/checkout@v2
      - name: run mbench
        uses: example/mbench@feat/testing-custom-github-actions
        with:
          id: "${{ github.event.inputs.benchmark-id }}"
          mem-limits: "${{ github.event.inputs.mem-limits }}"
          cpu-limits: "${{ github.event.inputs.cpu-limits }}"
          docker-block-image-url: "REDACTED.dkr.ecr.us-east-2.amazonaws.com/pca:${{ github.event.inputs.docker-block-image-tag }}"
          block-name: "pca"
          input-file-directory-path: "${{ github.event.inputs.input-file-directory-path }}"
```

### Viewing the Benchmark Results
Once the mbench benchmarks are completed, the results will be available on a Grafana dashboard.
This dashboard provides a visual representation of the maximum CPU, RAM, and runtime usage for the benchmarks run, enabling you to make informed decisions regarding pricing and Kubernetes resource limits.

You can access the results at: https://grafana.example.com/d/a4088651-9d6a-4e0b-8bef-8dcd03ed9436

This integration not only automates the benchmarking process but also centralizes the visibility of block performance, facilitating easier management and optimization of machine learning block resources
