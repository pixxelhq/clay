from clay import types


def test_clb_init() -> None:
    c = types.Callback(Id="123", State=types.ModelStates.FAILED)
    assert c.State == types.ModelStates.FAILED


def test_clb_serialise_dict() -> None:
    c = types.Callback(Id="task123", State=types.ModelStates.FAILED)
    d = c.model_dump(by_alias=True)
    assert d == {
        "id": "task123",
        "state": "TaskFailed",
        "err_msg": "",
        "inputs": None,
        "logs": "",
        "outputs": None,
        "user_logs": "",
    }
