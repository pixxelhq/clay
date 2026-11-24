---
title: Indicating Progress
order: 10
---

# Indicating Block Progress

A block can report how far its run has progressed, as a number from `0` to `100`. The Clay runner sends each update to the callback endpoint, so the orchestrator that runs the block can show it.

## How Progress Is Reported

* Progress is a number from `0` to `100`. It starts at `0`. After the block is set up and its inputs are downloaded, the runner reports `0`. When the run finishes, the success or failure callback reports `100`. In between, the block can report any value from `0` to `100`.

* If `setup` or the input download fails, the runner sends no callback at all, neither progress nor failure. The process exits with the exception. Errors after the `0` report, from input validation to the output upload, send a failure callback.

* The block reports progress with three methods:
    * `add_progress` — _A relative, additive method._
    * `set_progress` — _An absolute, setter method._
    * `get_progress` — _A read-only getter for the current progress value._

* The runner attaches these methods to the block after the block's constructor returns. The constructor runs `setup`, so inside `setup` the base class versions are used: `add_progress` and `set_progress` do nothing, and `get_progress` returns `None`. Report progress from `preprocess`, `inference` and `postprocess`.

* Each accepted update is sent as an HTTP `POST` to [`CALLBACK_ENDPOINT`](env-requirements.md#10-callback_endpoint), with the headers in [`CALLBACK_HEADERS`](env-requirements.md#11-callback_headers). The body looks like this:

    ```json
    {"data": {"id": "<EXECUTION_ID>", "progress": 40, "start_time": "2026-11-24T07:52:00.644807+00:00", "metadata": {}, "status": "inprogress"}}
    ```

    `id` is the value of [`EXECUTION_ID`](env-requirements.md#1-execution_id) and `start_time` is when the runner started, in UTC. A response with status `200`, `202` or `204` counts as success. Connection errors are retried up to 3 times. If the callback still fails, or the endpoint answers with another status, the runner logs an error and the block keeps running.

* Since the runner attaches these methods to your block instance, a function outside the block class cannot report progress unless you pass it the block. For example,

```python
from typing import Any, Dict

import datatypes
from clay.core import BlockWrapper


def some_function() -> None:
    # cannot indicate progress in this function without passing down `self`.
    pass


class Block(BlockWrapper):
    def setup(self, **kwargs: Any) -> None:
        pass

    # preprocess and postprocess omitted

    async def inference(self, a: datatypes.Raster) -> Dict[str, Any]:
        # can indicate progress here
        self.add_progress(5)

        # cannot indicate progress in `some_function` without passing down `self` into `some_function`.
        some_function()
        return {"a": a}
```

### `add_progress`

`add_progress(delta)` adds `delta` to the current progress and reports the new total. After a piece of code runs, pass the share of the whole run, in percent, that this code accounts for.

### `set_progress`

`set_progress(value)` sets the current progress to `value` and reports it. The value must pass the checks in [Rules of Thumb](#rules-of-thumb). Pass the progress you expect the run to have reached at that point in the code.

### `get_progress`

A read-only getter that returns the runner's current progress: `0.0` at the start, then the value of the last accepted update. After an `add_progress` call that pushes the total above `100`, it returns that total (see [Rules of Thumb](#rules-of-thumb)). Useful when you want to compute the next value relative to whatever the current progress happens to be — typically pairing with `set_progress` inside a loop:

```python
last = self.get_progress()
self.set_progress(last + per_iteration)
```

`get_progress` does not raise and does not send a callback.

## Rules of Thumb

* For loops and concurrent / parallel contexts, use the `add_progress` method.
    * In the case of for / do-while / while loops that are expected to run a set number of times, it is helpful to calculate a _progress per iteration_ and then use the `add_progress` method.

* For standard points in the program, where progress is expected to be deterministic and static, you can use the `set_progress` method.

* Out-of-range numbers do not stop the block. They are dropped and logged:
    * A value outside `0` to `100` (for `set_progress`), or a delta outside `0` to `100` (for `add_progress`), is ignored and logged as an error.
    * A `set_progress` value lower than the current progress is ignored and logged as a warning.
    * If `add_progress` would push the total above `100`, an error is logged and no update is sent. The internal counter still keeps the larger value, so `get_progress` returns more than `100` and later `set_progress` calls are rejected. Plan your deltas so they add up to `100` or less.
* A value that is not a number, such as a string or `None`, raises `TypeError`, and the run fails.

## Examples
### Simple usage of `add_progress`

```python
from typing import Any, Dict

import datatypes
from clay.core import BlockWrapper


class B(BlockWrapper):
    def setup(self, **kwargs: Any) -> None:
        pass

    async def preprocess(self, string: datatypes.String, raster: datatypes.Raster) -> Dict[str, Any]:
        total_iterations = 5  # example
        total_progress_at_the_end_of_for_loop = 20
        per_iteration = total_progress_at_the_end_of_for_loop / total_iterations
        for i in range(total_iterations):
            self.logger.info(f"iteration {i}")
            self.add_progress(per_iteration)
        return {"raster": raster.value, "string": string.value}

    async def inference(self, raster: str, string: str) -> Dict[str, Any]:
        output_raster = "clipped.tif"
        self.add_progress(15)
        return {"raster": output_raster, "string": "this is hello"}

    async def postprocess(self, raster: str, string: str) -> Dict[str, datatypes.Data]:
        self.add_progress(25)
        r = datatypes.Raster(name="result", type="url", value=raster)
        s = datatypes.String(name="string", value=string)
        return {
            "result": r,
            "string": s,
        }
```

### Simple usage of `set_progress`

!!! note

    In a loop, `set_progress` needs the last value on every iteration, as shown here. `add_progress` is simpler there.

```python
from typing import Any, Dict

import datatypes
from clay.core import BlockWrapper


class B(BlockWrapper):
    def setup(self, **kwargs: Any) -> None:
        pass

    async def preprocess(self, string: datatypes.String, raster: datatypes.Raster) -> Dict[str, Any]:
        total_iterations = 20
        total_progress_at_the_end_of_for_loop = 40
        per_iteration = total_progress_at_the_end_of_for_loop / total_iterations
        for i in range(total_iterations):
            self.logger.info(f"iteration {i}")
            last_progress = self.get_progress()
            self.set_progress(last_progress + per_iteration)
        return {"raster": raster.value, "string": string.value}

    async def inference(self, raster: str, string: str) -> Dict[str, Any]:
        output_raster = "clipped.tif"
        self.set_progress(45)
        return {"raster": output_raster, "string": "this is hello"}

    async def postprocess(self, raster: str, string: str) -> Dict[str, datatypes.Data]:
        self.set_progress(95)
        r = datatypes.Raster(name="result", type="url", value=raster)
        s = datatypes.String(name="string", value=string)
        return {
            "result": r,
            "string": s,
        }
```

### Setting progress from functions external to BlockWrapper

!!! warning

    Avoid this where you can. Passing `self` to other functions ties them to the block class. Prefer reporting progress from the block's own methods.

```python
from typing import Any, Dict

import datatypes
from clay.core import BlockWrapper


def external_function(block: BlockWrapper, some_param: int) -> int:
    block.add_progress(5)
    return some_param + 100


class B(BlockWrapper):
    def setup(self, **kwargs: Any) -> None:
        pass

    async def preprocess(self, string: datatypes.String, raster: datatypes.Raster) -> Dict[str, Any]:
        total_iterations = 20
        total_progress_at_the_end_of_for_loop = 40
        per_iteration = total_progress_at_the_end_of_for_loop / total_iterations
        for i in range(total_iterations):
            self.logger.info(f"iteration {i}")
            last_progress = self.get_progress()
            self.set_progress(last_progress + per_iteration)
        return {"raster": raster.value, "string": string.value}

    async def inference(self, raster: str, string: str) -> Dict[str, Any]:
        output_raster = "clipped.tif"
        self.set_progress(45)
        external_function(self, 123)
        return {"raster": output_raster, "string": "this is hello"}

    async def postprocess(self, raster: str, string: str) -> Dict[str, datatypes.Data]:
        self.set_progress(95)
        r = datatypes.Raster(name="result", type="url", value=raster)
        s = datatypes.String(name="string", value=string)
        return {
            "result": r,
            "string": s,
        }
```
