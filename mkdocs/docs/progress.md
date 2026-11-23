---
title: Indicating Progress
order: 10
---

# Indicating Block Progress

Many blocks run for a long time. Hence, indicating the progress of an inference is a key part of the user experience.

Indicating the progress of a process, block or not, is _generally a tricky process_ without any standardised way to do it. For example,

* Who should be reporting this progress? Should it be the process itself or some sort of manager process?
* If its the process, then how do we maintain state?
* How do we even _measure_ progress?
* How does all this work in concurrent environments?
* etc etc.

Well, we have outlined our approach with usage examples below.

## Our Approach

* The total progress of the block is bounded between 0 and 100, i.e. `[0, 100]`. Progress starts at `0`. Clay reports `0` when the run starts and `100` when it finishes (on success or failure). In between, the block can set any value from `0` to `100`.

* Clay exposes three progress APIs for the block author to use:
    * `add_progress` — _A relative, additive API._
    * `set_progress` — _An absolute, setter API._
    * `get_progress` — _A read-only getter for the current progress value._

* Progress is tracked by the Clay runner. When the runner creates your block, it attaches these three methods to it. Each accepted update is sent to the callback endpoint.

* Precision is welcomed wherever possible, but approximations also work.

* Since these methods are an attribute of the `BlockWrapper` class and by extension, the subclassed block, the methods cannot be used in a third party function, out of the box. For example,

```python
from typing import Any, Dict

import datatypes
from clay.core import BlockWrapper


def some_function() -> None:
    # cannot indicate progress in this function without passing down `self`.
    pass


class Block(BlockWrapper):
    async def inference(self, a: datatypes.Raster) -> Dict[str, Any]:
        # can indicate progress here
        self.add_progress(5)

        # cannot indicate progress in `some_function` without passing down `self` into `some_function`.
        some_function()
        return {"a": a}
```

### `add_progress`

Simply put, this is an _additive API_. Meaning, it simply _adds_ a certain value to whatever the existing progress of the block is. If you are going to use this endpoint to indicate the progress of the block, post the execution of a certain block of code, it is helpful to ask yourself, something like, _"How much % of the total execution of my block is this code block responsible for, approximately?"_. The answer is the input that you should send to `add_progress`.

### `set_progress`

This on the other hand, is an _absolute, setter API_. Meaning, it simply _set_ the current progress of the block to a particular value. Of-course, the value needs to pass a set of internal validations. If you intend to use this endpoint to indicate the progress of a block, post the execution of a block of code, it would be helpful to ask yourself a question like, _"What do I expect the current progress of execution to be at this particular point in my code?"_.

### `get_progress`

A read-only getter that returns the block's current progress as a `float`. Useful when you want to compute the next value relative to whatever the current progress happens to be — typically pairing with `set_progress` inside a loop:

```python
last = self.get_progress()
self.set_progress(last + per_iteration)
```

`get_progress` never raises and has no side effects.

## Rules of Thumb

* For loops and concurrent / parallel contexts, use the `add_progress` method.
    * In the case of for / do-while / while loops that are expected to run a set number of times, it is helpful to calculate a _progress per iteration_ and then use the `add_progress` method.

* For standard points in the program, where progress is expected to be deterministic and static, you can use the `set_progress` method.

* There is *never* going to be a runtime-exception because of progress reporting. Invalid values are dropped and logged:
    * A value outside `0` to `100` (for `set_progress`), or a delta outside `0` to `100` (for `add_progress`), is ignored and logged as an error.
    * A `set_progress` value lower than the current progress is ignored and logged as a warning.
    * If `add_progress` would push the total above `100`, an error is logged and no update is sent. The internal counter still keeps the larger value, so `get_progress` returns more than `100` and later `set_progress` calls are rejected. Plan your deltas so they add up to `100` or less.

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

    As you can see here, using `set_progress` within a loop is probably not a good idea and would require a lot of work, since in every iteration
    you have to indicate a current progress, meaning, you have to fetch the last value and then increment it with a certain value.

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

    Generally, try to avoid this as much as possible. Passing down `self` to external functions is generally considered
    an anti-pattern in the Python World.

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
