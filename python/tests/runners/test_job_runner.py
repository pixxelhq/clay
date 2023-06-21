import warnings

import pytest

from clay.runners import JobRunner

from ..models.noop import NOOP, NOOP_CONFIG, make_noop_input
from ..models.ymxplusc import YMXPLUSC, YMXPLUSC_CONFIG, make_ymxplusc_input


def test_jobrunner_ymxplusc() -> None:
    """
    Overall model integration test
    """
    model = JobRunner(YMXPLUSC.__name__, YMXPLUSC, {"config": YMXPLUSC_CONFIG})

    model_input = make_ymxplusc_input(x=5.0)
    with pytest.raises(SystemExit, match="0"):
        model.start([model_input])

    model_input = make_ymxplusc_input(x="hello")
    with pytest.raises(SystemExit, match="1"):
        warnings.warn(
            "TODO: Write tests to make sure logs are being sent to orchestrator when using"
            + " `clay.failure",
            category=UserWarning,
        )
        model.start([model_input])


def test_jobrunner_noop() -> None:
    """
    Overall model integration test
    """
    model = JobRunner(NOOP.__name__, NOOP, {"config": NOOP_CONFIG})

    model_input = make_noop_input(x=5.0)
    with pytest.raises(SystemExit, match="0"):
        model.start([model_input])

    model_input = make_ymxplusc_input(x="hello")
    with pytest.raises(SystemExit, match="1"):
        warnings.warn(
            "TODO: Write tests to make sure logs are being sent to orchestrator when using"
            + " `clay.failure",
            category=UserWarning,
        )
        model.start([model_input])
