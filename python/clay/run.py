import os
from typing import Type

from clay.core import ModelWrapper
from clay.runners.runner import JobRunner


def Run(model: Type[ModelWrapper], name: str, cfg_path: str) -> None:
    """The general method to execute a model. In most cases, users and programs alike
    should be using this method to run the model. The function looks at a bunch of internal
    environment variables and infers which runner *or execution mode* to use.
    This ensures that the execution mode of the model is abstracted away from the user.

    Args:
        model (Type[ModelWrapper]):
            The user defined model that subclasses `ModelWrapper`.
        name (str):
            Name of the model to be run. This is used as an identifier in the in-built logger.
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
        model_name=name,
        model_class=model,
        model_args={"config": cfg_path},
        cfg_path=cfg_path,
    )
    return runner.start()

