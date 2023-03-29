import pytest

from ramen.runners import JobRunner

from ..models.ymxplusc import YMXPLUSC, YMXPLUSC_CONFIG, make_ymxplusc_input


def test_jobrunner() -> None:
    """
    Overall model integration test
    """
    model = JobRunner(YMXPLUSC.__name__, YMXPLUSC, {"config": YMXPLUSC_CONFIG})

    model_input = make_ymxplusc_input(x=5.0)
    with pytest.raises(SystemExit, match="0"):
        model.start([model_input])

    model_input = make_ymxplusc_input(x="hello")
    with pytest.raises(SystemExit, match="1"):
        model.start([model_input])
