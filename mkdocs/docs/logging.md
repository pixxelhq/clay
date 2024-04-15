### Tip: logging helpful information

Clay provides logging functionality in `ModelWrapper` through it's `self.logger` attribute. You can and should use it to
print out useful information at various stages of the model pipeline.

We prefer using the `logger` instead of `print` statements because it provides a lot of extra information for free which
can be helpful during debugging.

Using the logger is very simple:

```python
# instead of this:
print("preprocessing complete")
```

```text
preprocessing complete
```

```python
# we do this:
self.logger.info("preprocessing complete")
```

```json
{
  "level": "INFO",
  "timestamp": "2024-03-21T05:28:27.435454Z",
  "logger": "DemoClay",
  "loc": "model.py:preprocess:67",
  "message": "preprocessing complete"
}
/* This has been formatted in multiple lines for the purposes of this doc.*/
/* The actual output is on a single line*/
```

As you can see, right off the bat we get some extra information with zero effort from our side:

- Level: the severity of the message.
    - This can be one of: `DEBUG`, `INFO`, `WARNING`, or `ERROR`, with severity increasing in that order
- Timestamp: the exact time at which this message was logged
- Logger: the name of the logger object used for this message. You will see other loggers from Clay printing other
  useful pieces of information as well.
- Loc[ation]: the exact file, function and line number of the location where the log was triggered
- Message: your actual log message

You can manually create loggers using clay very simply like so:

```python
import logging
from clay.logger import ClayLogger

logger = ClayLogger(logger_name='my-logger', level=logging.INFO)

logger.debug("This message will not be shown if level is set to INFO")
logger.info("This message and all messages at WARNING and ERROR level will be shown")
logger.warning("Warnings in scenarios such as when results can be computed but not necessarily with high quality")
logger.error("Reserved for situations where execution can generally not move forward", exc_info=exception_object)
```

You can learn more about [logging in python here](https://realpython.com/python-logging/)
