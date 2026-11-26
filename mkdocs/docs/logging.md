---
title: Logging
order: 12
---

# Logging

Clay provides structured JSON logging through the `BlockWrapper`'s `self.logger` attribute. Use it to print useful information at various stages of the block pipeline.

## Why Use Clay's Logger?

Use `self.logger` instead of `print`. Each log line is a JSON object with the level, the time, the logger name and the code location, which helps with debugging and monitoring.

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
| `level` | Severity of the message: `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL` |
| `timestamp` | Time the message was logged, in UTC, in ISO 8601 format ending in `Z` |
| `logger` | Name of the logger. `self.logger` is named after the block class. The runner's lines use the `name` passed to `clay.Run` in `entry.py`; generated projects pass the class name, so all lines show the same name |
| `loc` | File, function and line number of the logging call, as `file:function:line` |
| `message` | Your log message |

The fields always come in this order. If you log with `exc_info`, the JSON object is followed by plain text lines: the message again, then the traceback.

## Where Logs Go

The logger writes to standard output. In a generated project, `entry.py` calls `clay.Run`, which creates the runner's logger with level `DEBUG`. `entry.py` passes the block class name as `name`, so the block reuses the runner's logger: `DEBUG` messages from your block are shown, and so are the runner's `DEBUG` lines, such as each callback payload.

When the block is created, the log shows this `WARNING` line. It is expected, and comes from the block reusing the runner's logger:

```json
{"level": "WARNING", "timestamp": "2026-11-24T07:48:21.242794Z", "logger": "MyBlock", "loc": "logger.py:ClayLogger:238", "message": "Using existing logger without re-initialising."}
```

## Log Levels

Use the appropriate log level based on the message importance:

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed information for diagnosing problems |
| `INFO` | Confirmation that things are working as expected |
| `WARNING` | Something unexpected happened, but execution continues |
| `ERROR` | A serious problem that prevented an operation |
| `CRITICAL` | A more severe error than `ERROR`; logging it does not stop the block |

## Using the Logger in Blocks

The logger is available as `self.logger` in any `BlockWrapper` method:

```python
from typing import Any, Dict

import datatypes
from clay.core import BlockWrapper


class MyBlock(BlockWrapper):
    def setup(self, **parameters: Any) -> None:
        self.logger.info("Block initialized")

    async def preprocess(self, input_raster: datatypes.Raster) -> Dict[str, Any]:
        self.logger.info(f"Processing raster: {input_raster.value}")
        return {"raster_path": input_raster.value}

    async def inference(self, raster_path: str) -> Dict[str, Any]:
        self.logger.debug("Starting inference")
        result_path = raster_path  # ... inference logic ...
        self.logger.info("Inference complete")
        return {"result_path": result_path}

    async def postprocess(self, result_path: str) -> Dict[str, datatypes.Data]:
        if not result_path:
            self.logger.warning("Result path is empty")
        return {"output": datatypes.Raster(name="output", type="url", value=result_path)}
```

Every value returned from `postprocess` must be a datatype, such as `datatypes.Raster`.

## Creating Custom Loggers

You can create additional loggers using `ClayLogger`. It writes JSON lines to standard output, like `self.logger`. If a logger with the same name already exists, `ClayLogger` returns it unchanged, ignores `level`, and logs `Using existing logger without re-initialising.`

```python
import logging
from clay.logger import ClayLogger

# Create a custom logger
logger = ClayLogger(logger_name='my-custom-logger', level=logging.INFO)

# Use it anywhere in your code
logger.debug("This won't be shown if level is INFO")
logger.info("This will be shown")
logger.warning("Warnings for unexpected but non-fatal issues")

try:
    open("missing-file.txt")
except OSError as exc:
    logger.error("Errors when execution cannot proceed", exc_info=exc)
```

## Best Practices

- **Use `self.logger`** instead of `print()` statements
- **Choose appropriate log levels** - don't use `ERROR` for non-errors
- **Include context** - log variable values, file paths, and identifiers
- **Be concise** - log messages should be informative but not verbose
- **Log at boundaries** - log when entering/exiting major processing stages

## Further Reading

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
