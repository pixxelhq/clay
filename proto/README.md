# Proto Directory

This directory contains the protocol buffer definitions and language-specific client implementations for Pixxel's data types.

## Structure

```
proto/
├── data.proto          # Protocol buffer definitions
├── go/                 # Go client and wrappers
│   ├── generated/      # Auto-generated protobuf code
│   ├── main.go         # DataWrapper implementation
│   ├── main_test.go    # Tests
│   └── utils.go        # Utility functions
└── python/             # Python client and wrappers
    └── datatypes/      # Python package
        ├── data.py     # DataWrapper implementation
        ├── data_pb2.py # Auto-generated protobuf code
        └── tests/      # Tests
```

## Go Usage

```go
import "github.com/example/clay/proto/go"
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

The Python datatypes package is automatically published to AWS CodeArtifact when changes are pushed to the `proto/` directory. You can also manually trigger the workflow:

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
