# {{.Class}}

A block packaged with [Clay](https://github.com/pixxelhq/clay). The block code
is in `{{.Module}}/block.py`. Its parameters, inputs and outputs are in
`clay.yaml`.

## Set up

Use Python 3.10 or later.

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```
{{- if .WithPreCommit}}

Install the git hooks in `.pre-commit-config.yaml`:

```shell
pre-commit install
```
{{- end}}

## Test

Run the block locally with the inputs in `tests/sample_block_inputs.json`:

```shell
python tests/test_block.py
```

## Build and run

```shell
clay build
clay run {{.Slug}}:v0.0.1 --input "$(cat tests/sample_block_inputs.json)"
```

`clay build` tags the image with the `name` and `version` in `clay.yaml`.

## Dependencies
{{if .WithConda}}
- `conda.yaml`: the environment installed in the image (`build.requirements`
  in `clay.yaml`).
- `requirements.txt`: the runtime dependencies for local development.
{{- else}}
- `requirements.txt`: runtime dependencies. They are installed in the image.
{{- end}}
- `requirements-dev.txt`: development tools. They are never installed in the
  image.
