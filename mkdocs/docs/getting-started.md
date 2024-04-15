# Getting started

This section will guide you on how to use clay for project setup which will be used for model developement.

## Nomenclature
1. `clay` **CLI**: A command line tool which helps in model development by providing project scaffolding, dockerfile and deployment pipeline out of the box.
2. `clay` **Python SDK**: Used in the model development as a python dependency. 

## Prerequisite
* **macOS or Linux**: `clay` CLI is supported in macOS and Linux.
* **Docker**: Docker should be [installed](https://docs.docker.com/get-docker/) in your system. It will be used to build image and create container.
* **python**: You should have python >=3.9 installed in your system
* **git**: `git` should be installed in your system

## Project Setup
### Install clay CLI
`clay` is a private CLI for Pixxel hence we need to do authentication before installation. **You can just follow the commands blindly in choronological order.** 

1. Generate a Personal Access Token (PAT) (classic) on Github. You can follow Github's documentation [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic).

    * The minimum permissions are `repo`, `write:packages` and `read:packages`.

    !!! warning

        Treat your PAT's like passwords. In other words, be careful!

2. Copy the token and add it as a shell variable `HOMEBREW_GITHUB_API_TOKEN`.
```shell
export HOMEBREW_GITHUB_API_TOKEN=<replace-with-token-here>
```
    * For convenience, you can even add the above command your shell profile (eg: bashrc/zshrc etc), such that you don't have to repeat this step every time.

3. If you are on Linux/Ubuntu and your system doesn't have [Brew](https://brew.sh/), please install brew by following the instruction [here](https://docs.brew.sh/Homebrew-on-Linux).
    * Check if the installation worked by running `brew --version`. It should print something like, `Homebrew 4.2.12`.

4. The following command adds Pixxel's Brew Tap onto your system.
```shell
brew tap example/tap
```

5. Finally, install `Clay`.
```shell
brew install clay
```

6. Run `clay --version` to check and you should be good to go!

7. Use the following command to upgrade already installed clay.
```shell
brew upgrade clay
```

### Create Project
Let's say our model name is `DemoClay`
The following command would create the project in the current directory by default. If you want to create the project in some other directory, please feel free to provide the directory path instead of `.`

```shell
clay create project . DemoClay
```
Let's go into the `DemoClay` directory
```shell
cd Democlay
```



### Create your Python Virtual Environment

!!! important

    It is highly recommended to have a separate virtual environment for each model under development as it allows us to maintain clean dependency lists.
    
    For this demo we will use `pip` as package manager.

!!! warning

    It is very important to create a fresh virtual env before staring with the project. If you have already active virtural env please deactivate that.

Run the following command to create virtual env
```shell
python3 -m venv venv
```

Activate you venv by running the below command 
```shell
source venv/bin/activate
```

### Setup project 

Run the following command to setup your repository, this will initilize the `git` for you and install all the default dependencies like linters, formatters etc (mentioned in requirement-dev.txt).

```shell
make setup
```

### Install clay python SDK

#### Prerequisites

1. Install the AWS CLI onto your local machine. [[docs](https://aws.amazon.com/CLI/)]
2. Configure your CLI to login into the `d-core-services` cluster.
    * You can follow the [Cloud Team's documentation on this.](https://github.com/example/infra/blob/main/docs/aws/aws_CLI_guide.md)

The Clay python package is hosted on [AWS CodeArtifact](https://docs.aws.amazon.com/codeartifact/latest/ug/welcome.html).

The process is as follows,

1. Login to the aws using any profile. eg:
```shell
aws sso login --profile=d-analytics-sandbox
```

2. Once logged in, run this command,
```shell
export CODEARTIFACT_AUTH_TOKEN=`aws codeartifact get-authorization-token --domain REDACTED-ARTIFACTORY --domain-owner REDACTED-AWS-ACCT --query authorizationToken --region us-east-2 --output text`
```

    ??? Note "Pitfall"

        Depending on how your shell is configured, AWS might not be able detect the credentials. If even after successfully logging in, the AWS CLI is unable to find the creds, export this into your environment, `export AWS_PROFILE=<profile-name>` where <profile-name> is to be replaced with your AWS profile with which you logged in.

3. Run
```shell
pip install clay --extra-index-url=https://aws:$CODEARTIFACT_AUTH_TOKEN@REDACTED.d.codeartifact.us-east-2.amazonaws.com/pypi/python/simple/
```

### Build and run
1. Let's declare our dependency manager file. Go to `Democlay/Democlay/specifications/`, you will notice that there are three `yaml` file. Change the line no 49 in each file from `requirements: #requirements.txt or conda.yaml` to `requirements: requirement.txt`

!!! GPU

    If you want your model to run on GPU, it's recommended to use `conda.yaml` for handling dependencies. Clay utilizes conda for models with GPU support and ensures NVIDIA drivers are installed to enable GPU execution.

2. Create dockerfile
```shell
make dockerfile
```

3. Bulid docker [docker must be installed in your system]
```shell
make docker-image
```

4. Run dockerfile locally
```shell
make test-docker-image
```
the logs should look something like 
```
docker run testmodel "$(cat TestModel/sample_model_inputs.json)"
Using configuration located at: /app/specifications/model_specification_dev.yaml
WARNING - 2024-04-02 09:01:26,122 - job_runner.py:195 - job_model_runner - 'remote-prefix'
INFO - 2024-04-02 09:01:26,123 - core.py:346 - job_model_runner - Initializing model...
INFO - 2024-04-02 09:01:26,125 - core.py:348 - job_model_runner - Model initialization complete.
WARNING - 2024-04-02 09:01:27,130 - core.py:372 - job_model_runner - `ORCHESTRATOR_URL` not set, and hence not firing callback
ERROR - 2024-04-02 09:01:27,131 - job_runner.py:403 - job_model_runner - Failed to fire callback
WARNING - 2024-04-02 09:01:27,133 - model.py:22 - TestModel - In pre-process. Use self.logger for all logging. Avoid print statements
INFO - 2024-04-02 09:01:27,133 - model.py:25 - TestModel - Input1 is starting-point
INFO - 2024-04-02 09:01:27,133 - model.py:31 - TestModel - In inference. I can access all `self` parameters throughout the model
INFO - 2024-04-02 09:01:27,133 - model.py:36 - TestModel - In postprocessing
WARNING - 2024-04-02 09:01:27,138 - core.py:372 - job_model_runner - `ORCHESTRATOR_URL` not set, and hence not firing callback
WARNING - 2024-04-02 09:01:27,138 - job_runner.py:426 - job_model_runner - failed to fire callback successfully
INFO - 2024-04-02 09:01:27,138 - job_runner.py:470 - job_model_runner - results: [Number(Format='number', Type='int', Name='output1', Value=5, Default=None, IsArtifact=False)]
```

5. Time to do the initial commit. Run `git commit -m "feat: initial project setup"`

6. Ta da 🎉🎉🎉, your project setup is done. 

### Need GPUs

If your model runs on GPU then you need to make two changes in the spec file.

1. Update the `gpu` key. It will look something like
```yaml
  gpu:
    max: 1
```

2. Update the builds.requirements section to use conda.yaml for handling dependencies. Clay automatically uses conda for GPU models and ensures NVIDIA drivers are installed for GPU execution:
```yaml
build:
  python-version: "3.10"
  conda: true
  gdal: true
  apt-get:
  requirements: conda.yaml
```










