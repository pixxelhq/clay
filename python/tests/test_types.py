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


def test_init_raster_model_from_dict_success() -> None:
    d = {
        "format": "raster",
        "type": "url",
        "name": "raster",
        "value": "some.tiff",
        "properties": {"bands": ["B01", "B02"]},
    }

    r = types.Raster.model_validate(d)
    assert r.Properties.Bands == ["B01", "B02"]


def test_init_raster_model_from_dict_with_None_props_success() -> None:
    d = {
        "format": "raster",
        "type": "url",
        "name": "raster",
        "value": "some.tiff",
        "properties": None,
    }

    r = types.Raster.model_validate(d)
    assert r.Properties is None
