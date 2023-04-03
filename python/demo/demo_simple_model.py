# type: ignore
import time
from typing import Any, cast

from clay.core import ModelWrapper
from clay.logger import ClayLogger, get_streamvalues
from clay.runners import JobRunner


class DemoSimpleModel(ModelWrapper):
    def setup(self, arg1: int, arg2: str) -> None:
        self.arg1 = arg1
        self.arg2 = arg2
        time.sleep(1)
        self.logger = ClayLogger(
            "demo_model_logger",
            False,
            create_buffer_handler=True,
            create_console_handler=True,
        )
        self.logger.info("slept for a second there")

    async def preprocess(self, input1: str) -> Any:
        time.sleep(1)
        self.logger.warning("Was supposed to preprocss, but slept for a second there")
        return input1 + "B"

    async def inference(self, arg: str) -> Any:
        time.sleep(3)
        self.logger.error("inference was taking too long, not my fault")
        return arg + "C"

    async def postprocess(self, arg: str) -> Any:
        self.logger.critical("that was quick!!")
        logs = get_streamvalues(self.logger)
        return arg, logs


if __name__ == "__main__":
    # args = sys.argv[1]
    jr = JobRunner(
        "demo",
        cast(ModelWrapper, DemoSimpleModel),
        {"config": "demo/demo_simple_model_config.yaml"},
    )

    jr.start(['{"input1":"a"}'])
    # jr.start(args)
