from clay import _network, types
from clay.logger import ClayLogger


def test__fire_callback_to_dexter_returns_false_if_clb_url_not_found():
    _logger = ClayLogger("test-logger")
    val = _network._fire_callback_to_dexter(types.Callback(Id="123"), _logger, None, False)
    assert val is False
