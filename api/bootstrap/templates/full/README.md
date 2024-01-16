# {{.Name}}

This is an implementation of Pixxel's {{.Name}} model, wrapped within `Clay`

## Installation and Usage

First, make sure you have these environment variables setup on your machine:

- `GITLAB_TOKEN` (your Gitlab PAT to allow you to install `Clay`, `Matter`)
- `AZURE_TENANT_ID`, `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` (for the service account that will be used to access our cloud storage buckets)

### Easy way

- Run: `make package-and-test-model`

### Medium easy way

- First, Create a new Python environment with `GDAL` and install `Clay` from Pixxel's private Gitlab PIP Registry.<br>
  `pip install clay --index-url https://gitlab+deploy-token-1735743:${YOUR_GITLAB_TOKEN}@gitlab.com/api/v4/projects/38508365/packages/pypi/simple`
- Then, proceed to install the rest of the dependencies: `pip install -r requirements.txt`
- Run the model on sample inputs: `python {{.Name}}/test_model.py`
- OR
- Run: `cd tests && pytest -vs`

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.
