---
title: Logging
order: 12
---

# Logging

Clay provides structured JSON logging through the `BlockWrapper`'s `self.logger` attribute. Use it to print useful information at various stages of the block pipeline.

## Why Use Clay's Logger?

We prefer using the `logger` instead of `print` statements because it provides additional context for free, which is helpful during debugging and monitoring.

### Without Clay Logger

```python
print("preprocessing complete")
```

Output:
```text
preprocessing complete
```

### With Clay Logger

```python
self.logger.info("preprocessing complete")
```

Output:
```json
{
  "level": "INFO",
  "timestamp": "2024-03-21T05:28:27.435454Z",
  "logger": "DemoClay",
  "loc": "block.py:preprocess:67",
  "message": "preprocessing complete"
}
```

!!! note
    The JSON output is shown formatted here for readability. The actual output is on a single line.

## Log Fields

Clay's logger automatically includes:

| Field | Description |
|-------|-------------|
| `level` | Severity of the message: `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `timestamp` | Exact time the message was logged (ISO 8601 format) |
| `logger` | Name of the logger object (typically your block class name) |
| `loc` | File, function, and line number where the log was triggered |
| `message` | Your actual log message |

## Log Levels

Use the appropriate log level based on the message importance:

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed information for diagnosing problems |
| `INFO` | Confirmation that things are working as expected |
| `WARNING` | Something unexpected happened, but execution continues |
| `ERROR` | A serious problem that prevented an operation |

## Using the Logger in Blocks

The logger is available as `self.logger` in any `BlockWrapper` method:

```python
from clay.core import BlockWrapper
import datatypes

class MyBlock(BlockWrapper):
    def setup(self, **parameters):
        self.logger.info("Block initialized")

    async def preprocess(self, input_raster: datatypes.Raster):
        self.logger.info(f"Processing raster: {input_raster.value}")
        return {"raster": input_raster}

    async def inference(self, raster):
        self.logger.debug("Starting inference")
        # ... inference logic ...
        self.logger.info("Inference complete")
        return {"result": result}

    async def postprocess(self, result):
        if result is None:
            self.logger.warning("Result is None, returning empty output")
        return {"output": result}
```

## Creating Custom Loggers

You can create additional loggers using `ClayLogger`:

```python
import logging
from clay.logger import ClayLogger

# Create a custom logger
logger = ClayLogger(logger_name='my-custom-logger', level=logging.INFO)

# Use it anywhere in your code
logger.debug("This won't be shown if level is INFO")
logger.info("This will be shown")
logger.warning("Warnings for unexpected but non-fatal issues")
logger.error("Errors when execution cannot proceed", exc_info=exception_object)
```

## Best Practices

- **Use `self.logger`** instead of `print()` statements
- **Choose appropriate log levels** - don't use `ERROR` for non-errors
- **Include context** - log variable values, file paths, and identifiers
- **Be concise** - log messages should be informative but not verbose
- **Log at boundaries** - log when entering/exiting major processing stages

## Further Reading

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
