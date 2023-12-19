import os
import sys
from enum import Enum
from typing import Type, Union

from .core import ModelWrapper
from .runners.job_runner import JobRunner
from .runners.job_runner_v2 import JobRunnerV2
from .types import EXECUTOR_ENVVAR

_RunnerTypes = Union[JobRunner, JobRunnerV2]


class SupportedExecutors(Enum):
    ARGO = "argo"
    KUBE = "kube"
    LOCAL = "local"


__executor_runner_map__ = {
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
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(cfg_path)

    executor = _get_executor_type()
    v = __executor_runner_map__[executor]
    _runnercls: _RunnerTypes = v["runner"]
    requires_args: bool = v["requires_args"]
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
