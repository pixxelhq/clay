## Installation

Clay has two components,

1. [Python SDK](#python-sdk)
2. [CLI](#cli)


### Prerequisites

1. Install the AWS CLI onto your local machine. [[docs](https://aws.amazon.com/cli/)]
2. Configure your CLI to login into the `d-core-services` cluster.
    * You can follow the [Cloud Team's documentation on this.](https://github.com/example/infra/blob/main/docs/aws/aws_cli_guide.md)

### Python SDK

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

4. Run
```shell
pip config set global.extra-index-url https://aws:$CODEARTIFACT_AUTH_TOKEN@REDACTED.d.codeartifact.us-east-2.amazonaws.com/pypi/python/simple/
```

4. Finally, run the pip command to install clay
```shell
pip install clay
```

5. Done!

### CLI

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
