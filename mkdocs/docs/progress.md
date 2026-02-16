# Indicating Model Progress

Most of the models in our ecosystem are long running models. Hence, indicating the progress of an inference is a key component of the user experience.

Indicating the progress of a process, model or not, is _generally a tricky process_ without any standardised way to do it. For example,

* Who should be reporting this progress? Should it be the process itself or some sort of manager process?
* If its the process, then how do we maintain state?
* How do we even _measure_ progress?
* How does all this work in concurrent environments?
* etc etc.

Well, we have outlined our approach with usage examples below.

## Our Approach

* The total progress of the model is bounded between 0 and 100, i.e. `[0, 100]`. Of which, the model has access to the `(5, 95)` range. The ranges `[0, 5]` and `[95, 100]` are reserved by Clay.

* There are two types of API exposed by clay for the model author to use,
    * `add_progress` - _A relative, additive API._
    * `set_progress` - _An absolute, setter API._

* Progress is tracked, internally by the base `ModelWrapper` class, which is the base class for all models.

* Precision is welcomed wherever possible, but approximations also work.

* Since these methods are an attribute of the `ModelWrapper` class and by extension, the subclassed model, the methods cannot be used in a third party function, out of the box. For example,

```python
def some_function():
    # cannot indicate progress in this function without passing down `self`.

class Model(ModelWrapper):
    def inference(self, a: Raster):
        # can indicate progress here
        self.add_progress(5)

        # cannot indicate progress in `some_function` without passing down `self` into `some_function`.
        some_function()
```

### `add_progress`

Simply put, this is an _additive API_. Meaning, it simply _adds_ a certain value to whatever the existing progress of the model is. If you are going to use this endpoint to indicate the progress of the model, post the execution of a certain block of code, it is helpful to ask yourself, something like, _"How much % of the total execution of my model is this code block responsible for, approximately?"_. The answer is the input that you should send to `add_progress`.

### `set_progress`

This on the other hand, is an _absolute, setter API_. Meaning, it simply _set_ the current progress of the model to a particular value. Of-course, the value needs to pass a set of internal validations. If you intend to use this endpoint to indicate the progress of a model, post the execution of a block of code, it would be helpful to ask yourself a question like, _"What do I expect the current progress of execution to be at this particular point in my code?"_.

## Rules of Thumb

* For loops and concurrent / parallel contexts, use the `add_progress` method.
    * In the case of for / do-while / while loops that are expected to run a set number of times, it is helpful to calculate a _progress per iteration_ and then use the `add_progress` method.

* For standard points in the program, where progress is expected to be deterministic and static, you can use the `set_progress` method.

* There is *never* going to be a runtime-exception because of progress reporting. In-case of an invalid value, clay would simply ignore the value and log a warning.

## Examples
### Simple usage of `add_progress`

```python
class M(ModelWrapper):
    def __init__(
        self,
        config: str,
        protocol: str = "abfs",
        logger: Optional[Logger] = None,
        enable_debug_logs: Optional[bool] = None,
    ) -> None:
        super().__init__(config, protocol, logger, enable_debug_logs)

    def setup(self):
        pass

    async def preprocess(self, string, raster) -> Any:
        total_iterations = 5 # example
        total_progress_at_the_end_of_for_loop = 20
        per_iteration = total_progress_at_the_end_of_for_loop / total_iterations
        for i in range(total_iterations):
            print(i)
            self.add_progress(per_iteration)
        return {"raster": raster, "string": string}

    async def inference(self, raster, string) -> None:
        dummy_raster = pathlib.Path("../clipped.tiff")
        dummy_raster.touch()
        self.add_progress(15)
        return {"raster": str(dummy_raster), "string": "this is hello"}

    async def postprocess(self, raster, string) -> Any:
        self.add_progress(25)
        r = types.Raster(
            name="result",
            value=raster,
        )
        s = types.String(name="string", value=string)
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
class M(ModelWrapper):
    def __init__(
        self,
        config: str,
        protocol: str = "abfs",
        logger: Optional[Logger] = None,
        enable_debug_logs: Optional[bool] = None,
    ) -> None:
        super().__init__(config, protocol, logger, enable_debug_logs)

    def setup(self):
        pass

    async def preprocess(self, string, raster) -> Any:
        total_iterations = 20
        total_progress_at_the_end_of_forloop = 60
        per_iteration = total_iterations / total_progress_at_the_end_of_forloop
        for i in range(5):
            print(i)
            last_progress = self.get_progress()
            self.set_progress(last_progress + per_iteration)
        return {"raster": raster, "string": string}

    async def inference(self, raster, string) -> None:
        dummy_raster = pathlib.Path("../clipped.tiff")
        dummy_raster.touch()
        self.set_progress(45)
        return {"raster": str(dummy_raster), "string": "this is hello"}

    async def postprocess(self, raster, string) -> Any:
        self.set_progress(95)
        r = types.Raster(
            name="result",
            value=raster,
        )
        s = types.String(name="string", value=string)
        return {
            "result": r,
            "string": s,
        }

```

### Setting progress from functions external to ModelWrapper

!!! warning

    Generally, try to avoid this as much as possible. Passing down `self` to external functions is generally considered
    an anti-pattern in the Python World.

```python
def external_function(__model_self_, some_param: int) -> int:
    __model_self_.add_progress(5)
    return some_param + 100

class M(ModelWrapper):
    def __init__(
        self,
        config: str,
        protocol: str = "abfs",
        logger: Optional[Logger] = None,
        enable_debug_logs: Optional[bool] = None,
    ) -> None:
        super().__init__(config, protocol, logger, enable_debug_logs)

    def setup(self):
        pass

    async def preprocess(self, string, raster) -> Any:
        total_iterations = 20
        total_progress_at_the_end_of_forloop = 60
        per_iteration = total_iterations / total_progress_at_the_end_of_forloop
        for i in range(5):
            print(i)
            last_progress = self.get_progress()
            self.set_progress(last_progress + per_iteration)
        return {"raster": raster, "string": string}

    async def inference(self, raster, string) -> None:
        dummy_raster = pathlib.Path("../clipped.tiff")
        dummy_raster.touch()
        self.set_progress(45)
        external_function(self, 123)
        return {"raster": str(dummy_raster), "string": "this is hello"}

    async def postprocess(self, raster, string) -> Any:
        self.set_progress(95)
        r = types.Raster(
            name="result",
            value=raster,
        )
        s = types.String(name="string", value=string)
        return {
            "result": r,
            "string": s,
        }

```
