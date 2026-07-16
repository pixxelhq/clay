# Proto Directory

This directory contains the protocol buffer definitions and language-specific
client implementations for Clay's data types (rasters, vectors, scalars, and
other types that Clay blocks pass through their inputs and outputs).

## Structure

```
proto/
├── data.proto                      # Protocol buffer definitions
├── go/                             # Go client and wrappers
│   ├── generated/data.pb.go        # Auto-generated protobuf code
│   ├── main.go                     # DataWrapper implementation
│   ├── main_test.go                # Tests for DataWrapper
│   ├── utils.go                    # Top-level utility helpers
│   ├── utils_test.go               # Tests for utils
│   └── pkg/utils/                  # Reusable internal helpers (+ tests)
└── python/                         # Python client and wrappers
    ├── setup.py                    # Package metadata for `pixxel-datatypes`
    ├── requirements.txt            # Build/dev requirements
    └── datatypes/                  # Python package
        ├── __init__.py
        ├── __version__.py
        ├── data.py                 # DataWrapper implementation
        ├── data_pb2.py             # Auto-generated protobuf code
        ├── data_pb2.pyi            # Type stubs for generated code
        ├── py.typed                # PEP 561 marker
        └── tests/                  # Tests
```

## Go Usage

```go
import "github.com/pixxelhq/clay/proto/go"
```

## Python Usage

The Python datatypes package is published separately as `pixxel-datatypes` and can be installed via `uv` or `pip`:

```bash
uv pip install pixxel-datatypes
```

Then import in your code:

```python
import datatypes
from datatypes import DataWrapper
```

## Publishing

### Python Package

The Python datatypes package is published to PyPI as
[`pixxel-datatypes`](https://pypi.org/project/pixxel-datatypes/) by the
`publish-proto-python.yaml` GitHub workflow whenever changes land in
`proto/python/`. You can also trigger the workflow manually:

```bash
gh workflow run publish-proto-python.yaml
```

### Go Module

The Go datatypes are imported directly from this repository as a Go module dependency.

## Development

### Regenerating Protobuf Code

To regenerate the protobuf code after modifying `data.proto`:

**For Go:**
```bash
cd proto
protoc --go_out=./go/generated --go_opt=paths=source_relative data.proto
```

**For Python:**
```bash
cd proto
protoc --python_out=./python/datatypes --pyi_out=./python/datatypes data.proto
```

### Running Tests

**Go tests:**
```bash
cd proto/go
go test -v
```

**Python tests:**
```bash
cd proto/python
pytest datatypes/tests/ -v
```
