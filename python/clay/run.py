import os
import sys
from enum import Enum
from typing import Type, Union

from clay.core import ModelWrapper
from clay.runners.job_runner import JobRunner
from clay.runners.job_runner_v2 import JobRunnerV2
from clay.types import EXECUTOR_ENVVAR

_RunnerTypes = Union[JobRunner, JobRunnerV2]


class SupportedExecutors(Enum):
    """
    Supported execution modes for the model.

    Attributes:
        ARGO (str):
            Model to be executed in `argo` mode. Only used by
            `Orchestrator` to run the model as a part of a workflow.
        KUBE (str):
            Model to be executed in `kube` mode. Can be used to
            run the model on a local machine or as a job on K8s.
        LOCAL (str):
            Model to be executed in `local` mode. Usually the mode
            when model is to be run on a local machine.

    """

    ARGO = "argo"
    KUBE = "kube"
    LOCAL = "local"


_executor_runner_map = {
    SupportedExecutors.ARGO: {"runner": JobRunnerV2, "requires_args": False},
    SupportedExecutors.KUBE: {"runner": JobRunner, "requires_args": True},
    SupportedExecutors.LOCAL: {"runner": JobRunner, "requires_args": True},
}


def _get_executor_type() -> SupportedExecutors:
    executor = os.getenv(EXECUTOR_ENVVAR)
    if executor is None:
        return SupportedExecutors.LOCAL
    if executor == SupportedExecutors.ARGO.value:
        return SupportedExecutors.ARGO
    elif executor == SupportedExecutors.KUBE.value:
        return SupportedExecutors.KUBE
    else:
        raise ValueError(f"unknown executor type: `{executor}`")


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

    executor = _get_executor_type()
    v = _executor_runner_map[executor]
    _runnercls: _RunnerTypes = v["runner"]  # type: ignore
    requires_args: bool = v["requires_args"]  # type: ignore
    _runnerobj: _RunnerTypes = _runnercls(
        model_name=name,
        modelcls=model,
        model_args={"config": cfg_path},
        cfg_path=cfg_path,
    )  # type: ignore

    if requires_args:
        args = sys.argv[1]
        if len(args) <= 1:
            raise ValueError(f"executor type `{executor.value}` requires args")
        return _runnerobj.start(args=args)

    return _runnerobj.start()
