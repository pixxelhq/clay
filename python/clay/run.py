import os
from typing import Type

from clay.core import BlockWrapper
from clay.runners.runner import JobRunner


def Run(block: Type[BlockWrapper], name: str, cfg_path: str) -> None:
    """The general method to execute a block. In most cases, users and programs alike
    should be using this method to run the block. The function looks at a bunch of internal
    environment variables and infers which runner *or execution mode* to use.
    This ensures that the execution mode of the block is abstracted away from the user.

    Args:
        block (Type[BlockWrapper]):
            The user defined block that subclasses `BlockWrapper`.
        name (str):
            Name of the block to be run. This is used as an identifier in the in-built logger.
        cfg_path (str): Path to the configuration that is meant to be used.

    Raises:
        FileNotFoundError:
            Raised when `cfg_path` does not exist.
        ValueError:
            Raised when the runner requires a set of command line arguments but no arguments
            were provided.
    """
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(cfg_path)
    runner = JobRunner(
        block_name=name,
        block_class=block,
        block_args={"config": cfg_path},
        cfg_path=cfg_path,
    )
    return runner.start()

